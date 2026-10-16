"""
Tests para formularios base reutilizables de apps/core.
"""

from django import forms

from apps.core.forms import HoneypotMixin


class _DummyForm(HoneypotMixin):
    """Form mínimo para testear el mixin de forma aislada."""

    name = forms.CharField(required=True)


class TestHoneypotMixin:
    def test_formulario_valido_sin_completar_el_honeypot(self):
        form = _DummyForm(data={"name": "Juan"})

        assert form.is_valid()

    def test_formulario_invalido_si_el_honeypot_viene_completado(self):
        form = _DummyForm(data={"name": "Juan", "website": "http://spam.example.com"})

        assert not form.is_valid()
        assert "website" in form.errors

    def test_el_campo_website_no_es_requerido(self):
        form = _DummyForm(data={"name": "Juan"})
        form.is_valid()

        assert not form.fields["website"].required
