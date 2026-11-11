# Guía de testing

Tests del backend (pytest) y de la app mobile (flutter test). Antes de pasar algo a `main`, la suite completa tiene que pasar: es lo mismo que corre CI.

---

## Backend (pytest)

La configuración está en `pyproject.toml`. Cada corrida ya incluye, sin pasarlo a mano:

- `DJANGO_SETTINGS_MODULE=config.settings.dev`, con SQLite.
- `--reuse-db` y `--nomigrations`: la base de test se crea desde los modelos y se reutiliza entre corridas.
- Coverage de `apps/` con mínimo de **80 %** (`--cov-fail-under=80`): si baja, la corrida falla aunque pasen todos los tests.

### Comandos

```bash
pytest -q                                                    # suite completa (~9 min)
pytest apps/expenses/ -q                                     # una app
pytest apps/expenses/tests/test_views.py -q                  # un archivo
pytest apps/expenses/tests/test_views.py::TestClase::test_x -q   # un test
pytest -k "rollover" -q                                      # por nombre
pytest -x --lf -q                                            # repetir solo los que fallaron, cortando en el primero
```

Al correr un solo archivo, el coverage total queda bajo y pytest lo marca como fallo. Para iterar rápido sobre un archivo: `pytest ruta -q --no-cov`.

Reportes de coverage:

```bash
pytest --cov-report=term-missing   # líneas sin cubrir en la terminal
pytest --cov-report=html           # htmlcov/index.html
```

### Markers

| Marker | Uso |
|---|---|
| `slow` | Tests lentos. Excluirlos: `pytest -m "not slow"` |
| `integration` | Flujos completos (`apps/core/tests/integration/`). Solo esos: `pytest -m integration` |

`--strict-markers` está activo: un marker que no esté declarado en `pyproject.toml` hace fallar la corrida.

### Convenciones

- **Clases y nombres:** `TestXxxYyy` con métodos `test_...`.
- **Fixtures:** las comunes están en el `conftest.py` de la raíz (`user`, `other_user`, `authenticated_client`, `expense_category`, `expense_factory`, `income_factory`, fechas como `today` y `last_month`). Las de una sola app, en el `conftest.py` de esa app o en el mismo archivo de test.
- **Base real, sin mocks de la DB:** los tests usan SQLite de verdad. Se mockean solo los servicios externos: Brevo (`apps.core.utils.send_brevo_email` o donde se importe), Firebase y la cotización del dólar.
- **Colores de categoría:** usar solo los de `CATEGORY_COLOR_CHOICES` (por ejemplo `#dc3545`, `#28a745`, `#6c757d`).
- **Mensajes toast:** `client.post(..., follow=True)` y leer `response.context["messages"]`.
- **Cantidad de queries:** `django_assert_max_num_queries` (ejemplos en `apps/reports/tests/test_queries_dashboard.py`).
- **API:** el token se obtiene con un `POST /api/v1/auth/token/` (ver `auth_header` en `apps/api/tests/test_dashboard.py`).
- **Emails:** con Brevo mockeado, el fallback de Django queda en la fixture `mailoutbox`.

### Qué cubrir

- Lógica de negocio nueva o modificada: siempre con tests.
- Vistas, formularios y permisos: el caso exitoso y el caso no permitido (otro usuario, sin login).
- Fechas, meses y períodos: casos borde (fin de mes, mes financiero que no empieza el 1, cambio de año). Los tests corren en SQLite y producción en PostgreSQL, que no tratan igual las fechas y las agregaciones.
- Un bug corregido: un test que falle sin el arreglo.

---

## Mobile (Flutter)

Desde `mobile/`:

```bash
flutter test                                      # todos (~10 s)
flutter test test/widget/login_screen_test.dart   # uno
flutter analyze                                   # análisis estático
```

| Carpeta | Qué testea |
|---|---|
| `test/unit/` | Providers y servicios, con repositorios mockeados |
| `test/widget/` | Pantallas y widgets montados con `pumpWidget` |

Los mocks se generan con mockito (`@GenerateMocks`) en archivos `*.mocks.dart` que se commitean. Después de cambiar una clase mockeada:

```bash
dart run build_runner build --delete-conflicting-outputs
```

Patrones para tests de widgets:

- **Riverpod:** envolver en `ProviderScope(overrides: [...])`. Montos ocultos: override de `amountsHiddenProvider` con una subclase de `AmountsVisibilityNotifier`.
- **Tema:** `ThemeData(extensions: const [AppSemanticColors.light])`, porque los widgets leen sus colores del tema.
- **Pantallas angostas y fuente grande:** fijar `tester.view.physicalSize` y `MediaQueryData(textScaler: TextScaler.linear(1.3))`, y verificar `tester.takeException()` es `null` (ver `projection_banner_test.dart`).

---

## Limpieza

```bash
pytest --cache-clear       # caché de pytest
pytest --create-db -q      # recrear la base de test (después de cambiar modelos)
```

Si un cambio de modelos no se refleja en los tests, casi siempre es la base reutilizada: correr con `--create-db`.
