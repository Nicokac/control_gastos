from django.utils import timezone

import pytest


@pytest.mark.django_db
class TestExpenseListQueries:
    def test_expense_list_query_count_is_bounded(self, client_logged, expense_factory):
        """
        Baseline: el listado NO debe degradar a N+1.

        Nota: este número puede ajustarse si el template agrega cosas.
        La idea es detectar regresiones (subidas grandes), no micro-optimizar.
        """
        today = timezone.now().date()

        # Crear suficientes gastos para detectar N+1 si existiera
        for _ in range(30):
            expense_factory(date=today)

        # IMPORTANTE:
        # Ajustar el número luego de medir una vez (ver paso 2).
        # Arrancamos con un budget "razonable" para list + filtros + aggregates.
        with pytest.raises(AssertionError):
            # placeholder para que NO pase “de casualidad” sin que fijemos baseline real
            # (en el paso 2 medimos y reemplazamos por self.assertNumQueries(N))
            pytest.fail("TODO: definir baseline real de queries y reemplazar por assert de conteo")
