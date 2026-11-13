import re
from pathlib import Path

from django.conf import settings
from django.urls import reverse

import pytest

from apps.shared_expenses.models import HouseholdMember

INLINE_HANDLER = re.compile(r"\son[a-z]+\s*=", re.IGNORECASE)


class TestTemplatesWithoutInlineHandlers:
    def test_no_template_uses_inline_event_handlers(self):
        offenders = []
        base = Path(settings.BASE_DIR)
        paths = [*base.glob("templates/**/*.html"), *base.glob("apps/**/templates/**/*.html")]
        for path in paths:
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if INLINE_HANDLER.search(line):
                    offenders.append(f"{path.relative_to(settings.BASE_DIR)}:{lineno}")
        assert offenders == []


@pytest.mark.django_db
class TestCspSafeBehaviors:
    def test_member_delete_form_uses_data_confirm(self, authenticated_client, user):
        HouseholdMember.objects.create(user=user, name="D'Angelo")
        response = authenticated_client.get(reverse("shared_expenses:members"))
        content = response.content.decode()
        assert 'data-confirm="¿Eliminar a D&#x27;Angelo?"' in content
        assert "onclick" not in content

    def test_annual_report_year_select_autosubmits(self, authenticated_client):
        response = authenticated_client.get(reverse("reports:annual"))
        assert 'name="year"' in response.content.decode()
        assert "data-autosubmit" in response.content.decode()
