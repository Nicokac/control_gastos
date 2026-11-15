import json
from decimal import Decimal

from django.urls import reverse

import pytest

from apps.categories.models import CategoryOverride, CategoryRule
from apps.categories.rules import find_rule, learn_rule, normalize_text
from apps.core.constants import PaymentMethod
from apps.expenses.importers import ImportedRow
from apps.expenses.models import Expense
from apps.expenses.quick_entry import parse_quick_expense
from apps.expenses.views import _build_import_preview


@pytest.fixture
def supermarket(user, expense_category_factory):
    return expense_category_factory(user=user, name="Supermercado", color="#28a745")


@pytest.fixture
def gifts(user, expense_category_factory):
    return expense_category_factory(user=user, name="Regalos", color="#d63384")


@pytest.fixture
def rule_factory(user):
    def _create(pattern, category, owner=None):
        return CategoryRule.objects.create(user=owner or user, pattern=pattern, category=category)

    return _create


class TestNormalizeText:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("Super COTO", "super coto"),
            ("Farmacía", "farmacia"),
            ("MERPAGO*KIOSCO 4821", "merpago kiosco 4821"),
            ("  netflix.com  ", "netflix com"),
            ("***", ""),
            (None, ""),
        ],
    )
    def test_normalizes(self, text, expected):
        assert normalize_text(text) == expected


@pytest.mark.django_db
class TestFindRule:
    def test_matches_whole_words_ignoring_case_and_accents(self, user, supermarket, rule_factory):
        rule = rule_factory("super", supermarket)

        assert find_rule(user, "Súper Coto") == rule
        assert find_rule(user, "superpancho") is None

    def test_multiword_rule_needs_the_words_together(self, user, supermarket, rule_factory):
        rule_factory("super coto", supermarket)

        assert find_rule(user, "compra super coto palermo") is not None
        assert find_rule(user, "coto super") is None

    def test_most_specific_rule_wins(self, user, supermarket, gifts, rule_factory):
        rule_factory("super", supermarket)
        specific = rule_factory("super regalo", gifts)

        assert find_rule(user, "super regalo tia") == specific
        assert find_rule(user, "super coto").category == supermarket

    def test_ignores_other_users_rules(
        self, user, other_user, expense_category_factory, rule_factory
    ):
        theirs = expense_category_factory(user=other_user, name="Ajena")
        rule_factory("super", theirs, owner=other_user)

        assert find_rule(user, "super") is None

    def test_ignores_rules_with_hidden_category(self, user, system_expense_category, rule_factory):
        rule_factory("super", system_expense_category)
        CategoryOverride.objects.create(user=user, category=system_expense_category, is_hidden=True)

        assert find_rule(user, "super") is None

    def test_deleting_category_deletes_its_rules(self, user, gifts, rule_factory):
        rule_factory("regalo", gifts)

        gifts.delete()

        assert not CategoryRule.objects.exists()


@pytest.mark.django_db
class TestLearnRule:
    def test_creates_rule_from_normalized_text(self, user, gifts):
        rule = learn_rule(user, "Regalo cumpleaños", gifts)

        assert rule.pattern == "regalo cumpleanos"
        assert rule.category == gifts

    def test_updates_existing_rule(self, user, supermarket, gifts, rule_factory):
        rule_factory("super", supermarket)

        learn_rule(user, "Super", gifts)

        assert CategoryRule.objects.get().category == gifts

    def test_empty_text_creates_nothing(self, user, gifts):
        assert learn_rule(user, " ** ", gifts) is None
        assert not CategoryRule.objects.exists()

    def test_long_text_is_cut_at_a_word(self, user, gifts):
        rule = learn_rule(user, "palabra " * 30, gifts)

        assert len(rule.pattern) <= 100
        assert rule.pattern.endswith("palabra")


@pytest.mark.django_db
class TestQuickEntryWithRules:
    def test_rule_beats_history_and_name(
        self, user, supermarket, gifts, rule_factory, expense_factory
    ):
        expense_factory(user, supermarket, description="super")
        rule_factory("super", gifts)

        parsed = parse_quick_expense(user, "15000 super")

        assert parsed.category == gifts
        assert parsed.category_source == "regla"
        assert parsed.category_rule == "super"

    def test_preview_includes_rule(self, authenticated_client, gifts, rule_factory):
        rule_factory("regalo", gifts)

        data = authenticated_client.post(
            reverse("expenses:quick_parse"),
            {"text": "5000 regalo tia"},
            content_type="application/json",
        ).json()

        assert data["category_id"] == gifts.pk
        assert data["category_source"] == "regla"
        assert data["category_rule"] == "regalo"


@pytest.mark.django_db
class TestQuickCreateLearnsRules:
    url = reverse("expenses:quick_create")

    def post(self, client, category, suggested="", description="regalo cumple"):
        return client.post(
            self.url,
            {
                "amount": "5000",
                "currency": "ARS",
                "exchange_rate": "1",
                "date": "2026-11-12",
                "payment_method": PaymentMethod.CASH,
                "description": description,
                "category": category.pk,
                "suggested_category": suggested,
                "next": reverse("expenses:list"),
            },
            follow=True,
        )

    def test_changing_the_suggestion_learns_a_rule(
        self, authenticated_client, user, supermarket, gifts
    ):
        response = self.post(authenticated_client, gifts, suggested=str(supermarket.pk))

        rule = CategoryRule.objects.get(user=user)
        assert (rule.pattern, rule.category) == ("regalo cumple", gifts)
        messages = [str(m) for m in response.context["messages"]]
        assert any("Desde ahora, “regalo cumple” se sugiere en Regalos" in m for m in messages)

    def test_choosing_without_suggestion_learns_a_rule(self, authenticated_client, gifts):
        self.post(authenticated_client, gifts)

        assert CategoryRule.objects.get().category == gifts

    def test_keeping_the_suggestion_learns_nothing(self, authenticated_client, gifts):
        self.post(authenticated_client, gifts, suggested=str(gifts.pk))

        assert not CategoryRule.objects.exists()

    def test_without_description_learns_nothing(self, authenticated_client, gifts):
        self.post(authenticated_client, gifts, description="")

        assert Expense.objects.exists()
        assert not CategoryRule.objects.exists()

    def test_invalid_expense_learns_nothing(
        self, authenticated_client, other_user, expense_category_factory
    ):
        theirs = expense_category_factory(user=other_user, name="Ajena")

        self.post(authenticated_client, theirs)

        assert not CategoryRule.objects.exists()


@pytest.mark.django_db
class TestImportWithRules:
    def imported(self, description, **overrides):
        values = {
            "raw_date": "05.07.26",
            "description": description,
            "amount": Decimal("8500.00"),
            "currency": "ARS",
        }
        values.update(overrides)
        return ImportedRow(**values)

    def test_preview_rule_beats_history(
        self, user, supermarket, gifts, rule_factory, expense_factory
    ):
        expense_factory(user, supermarket, description="MERPAGO*KIOSCO 4821")
        rule_factory("kiosco", gifts)

        row = _build_import_preview([self.imported("MERPAGO*KIOSCO 4821")], user, [])[0]

        assert row["suggested_category_pk"] == gifts.pk
        assert row["suggested_rule"] == "kiosco"

    def test_preview_without_rule_keeps_history(self, user, supermarket, expense_factory):
        expense_factory(user, supermarket, description="COTO")

        row = _build_import_preview([self.imported("COTO")], user, [])[0]

        assert row["suggested_category_pk"] == supermarket.pk
        assert row["suggested_rule"] == ""

    def confirm(self, client, **overrides):
        row = {
            "include": True,
            "date": "05.07.26",
            "description": "COTO 123",
            "source_description": "COTO 123",
            "amount": "8500.00",
            "currency": "ARS",
            "category_pk": "",
            "suggested_category_pk": "",
            "exchange_rate": "",
            "type": "punctual",
            "installment_current": "",
            "installment_total": "",
        }
        row.update(overrides)
        return client.post(
            reverse("expenses:import_confirm"), {"rows_json": json.dumps([row])}, follow=True
        )

    def test_correcting_a_suggestion_learns_from_original_description(
        self, authenticated_client, user, supermarket, gifts
    ):
        response = self.confirm(
            authenticated_client,
            description="Regalo editado",
            category_pk=str(gifts.pk),
            suggested_category_pk=str(supermarket.pk),
        )

        rule = CategoryRule.objects.get(user=user)
        assert (rule.pattern, rule.category) == ("coto 123", gifts)
        messages = [str(m) for m in response.context["messages"]]
        assert any("Guardamos 1 regla" in m for m in messages)

    def test_row_without_suggestion_learns_nothing(self, authenticated_client, gifts):
        self.confirm(authenticated_client, category_pk=str(gifts.pk))

        assert Expense.objects.exists()
        assert not CategoryRule.objects.exists()

    def test_kept_suggestion_learns_nothing(self, authenticated_client, gifts):
        self.confirm(
            authenticated_client, category_pk=str(gifts.pk), suggested_category_pk=str(gifts.pk)
        )

        assert not CategoryRule.objects.exists()

    def test_excluded_row_learns_nothing(self, authenticated_client, supermarket, gifts):
        self.confirm(
            authenticated_client,
            include=False,
            category_pk=str(gifts.pk),
            suggested_category_pk=str(supermarket.pk),
        )

        assert not CategoryRule.objects.exists()


@pytest.mark.django_db
class TestRuleViews:
    def test_list_requires_login(self, client):
        response = client.get(reverse("categories:rules"))

        assert response.status_code == 302
        assert "login" in response.url

    def test_list_shows_only_own_rules(
        self, authenticated_client, other_user, gifts, expense_category_factory, rule_factory
    ):
        theirs = expense_category_factory(user=other_user, name="Ajena")
        rule_factory("regalo", gifts)
        rule_factory("secreto", theirs, owner=other_user)

        content = authenticated_client.get(reverse("categories:rules")).content.decode()

        assert "regalo" in content
        assert "secreto" not in content

    def test_category_list_links_to_rules(self, authenticated_client):
        content = authenticated_client.get(reverse("categories:list")).content.decode()

        assert reverse("categories:rules") in content

    def test_create_normalizes_pattern(self, authenticated_client, user, gifts):
        response = authenticated_client.post(
            reverse("categories:rule_create"),
            {"pattern": "  Regalo  Cumpleaños ", "category": gifts.pk},
            follow=True,
        )

        rule = CategoryRule.objects.get()
        assert (rule.user, rule.pattern, rule.category) == (user, "regalo cumpleanos", gifts)
        assert response.redirect_chain[-1][0] == reverse("categories:rules")

    def test_create_rejects_duplicate(self, authenticated_client, gifts, rule_factory):
        rule_factory("regalo", gifts)

        response = authenticated_client.post(
            reverse("categories:rule_create"), {"pattern": "REGALO", "category": gifts.pk}
        )

        assert response.status_code == 200
        assert "Ya tenés una regla con ese texto." in response.content.decode()
        assert CategoryRule.objects.count() == 1

    def test_create_rejects_empty_pattern(self, authenticated_client, gifts):
        response = authenticated_client.post(
            reverse("categories:rule_create"), {"pattern": "***", "category": gifts.pk}
        )

        assert response.status_code == 200
        assert not CategoryRule.objects.exists()

    def test_create_rejects_other_users_category(
        self, authenticated_client, other_user, expense_category_factory
    ):
        theirs = expense_category_factory(user=other_user, name="Ajena")

        authenticated_client.post(
            reverse("categories:rule_create"), {"pattern": "super", "category": theirs.pk}
        )

        assert not CategoryRule.objects.exists()

    def test_update(self, authenticated_client, supermarket, gifts, rule_factory):
        rule = rule_factory("merpago kiosco 4821", supermarket)

        authenticated_client.post(
            reverse("categories:rule_update", args=[rule.pk]),
            {"pattern": "kiosco", "category": gifts.pk},
        )

        rule.refresh_from_db()
        assert (rule.pattern, rule.category) == ("kiosco", gifts)

    def test_update_keeps_own_pattern(self, authenticated_client, gifts, rule_factory):
        rule = rule_factory("regalo", gifts)

        response = authenticated_client.post(
            reverse("categories:rule_update", args=[rule.pk]),
            {"pattern": "regalo", "category": gifts.pk},
        )

        assert response.status_code == 302

    def test_delete(self, authenticated_client, gifts, rule_factory):
        rule = rule_factory("regalo", gifts)

        response = authenticated_client.post(
            reverse("categories:rule_delete", args=[rule.pk]), follow=True
        )

        assert not CategoryRule.objects.exists()
        messages = [str(m) for m in response.context["messages"]]
        assert any("eliminada" in m for m in messages)

    def test_delete_by_get_not_allowed(self, authenticated_client, gifts, rule_factory):
        rule = rule_factory("regalo", gifts)

        response = authenticated_client.get(reverse("categories:rule_delete", args=[rule.pk]))

        assert response.status_code == 405

    def test_cannot_touch_other_users_rule(
        self, authenticated_client, other_user, expense_category_factory, rule_factory
    ):
        theirs = expense_category_factory(user=other_user, name="Ajena")
        rule = rule_factory("secreto", theirs, owner=other_user)

        edit = authenticated_client.get(reverse("categories:rule_update", args=[rule.pk]))
        delete = authenticated_client.post(reverse("categories:rule_delete", args=[rule.pk]))

        assert edit.status_code == 404
        assert delete.status_code == 404
        assert CategoryRule.objects.filter(pk=rule.pk).exists()
