import re

from django.conf import settings

# Argentina es UTC-3: de 21 a 24 hs la fecha UTC ya es "mañana" y los tests de "mes actual" fallan (DT-064).
FORBIDDEN = re.compile(
    r"timezone\.now\(\)\.(date|year|month|day)\b|(?<![\w.])date\.today\(\)|datetime\.today\(\)"
)


class TestDatesInTests:
    def test_los_tests_usan_localdate(self):
        files = [settings.BASE_DIR / "conftest.py", *settings.BASE_DIR.glob("apps/**/test*.py")]
        offenders = [
            f"{path.relative_to(settings.BASE_DIR)}:{lineno}"
            for path in files
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
            if FORBIDDEN.search(line)
        ]
        assert not offenders, (
            f"Usar timezone.localdate() en vez de la fecha UTC o del sistema: {offenders}"
        )
