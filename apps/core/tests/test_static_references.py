import re

from django.conf import settings
from django.contrib.staticfiles import finders

STATIC_TAG = re.compile(r"""\{%\s*static\s+['"]([^'"]+)['"]""")


class TestStaticReferences:
    def test_todo_static_de_los_templates_existe(self):
        # En producción el manifest de WhiteNoise da 500 si un {% static %} apunta a un archivo inexistente.
        referencias = {
            (path.relative_to(settings.BASE_DIR), ref)
            for path in (settings.BASE_DIR / "templates").rglob("*.html")
            for ref in STATIC_TAG.findall(path.read_text(encoding="utf-8"))
        }

        faltantes = [(str(path), ref) for path, ref in sorted(referencias) if not finders.find(ref)]

        assert referencias
        assert faltantes == []
