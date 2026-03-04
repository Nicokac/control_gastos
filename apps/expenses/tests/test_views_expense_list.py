from django.urls import reverse

import pytest

from apps.expenses.views import ExpenseListView


@pytest.mark.django_db
def test_expense_listview_calls_get_queryset_once(client, user, monkeypatch):
    client.force_login(user)

    calls = {"n": 0}
    original = ExpenseListView.get_queryset

    def wrapped(self, *args, **kwargs):
        calls["n"] += 1
        return original(self, *args, **kwargs)

    monkeypatch.setattr(ExpenseListView, "get_queryset", wrapped)

    resp = client.get(reverse("expenses:list"))
    assert resp.status_code == 200
    assert calls["n"] == 1
