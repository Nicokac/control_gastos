# Auditoría de seguridad

Checklist de seguridad del proyecto, auditado contra el código real (no es una
lista genérica — cada ítem tiene evidencia concreta o referencia a dónde
verificarlo). Dos rondas:

- **Ronda 1** (2026-10-16): 20 puntos, checklist básico. Resultó en 3 fixes:
  [DT-093](DECISIONS.md), DT-094, DT-095.
- **Ronda 2** (2026-10-16): 14 puntos adicionales (CSRF, CORS, RBAC, MFA,
  gestión de tokens, backups, CI, etc.).

Convención: ✅ resuelto/correcto · ⚠️ parcial o con matiz · ❌ falta · N/A no
aplica a esta app. Prioridad solo se indica cuando hay algo pendiente.

---

## Ronda 1 — Checklist básico

### 1. Ocultar API keys — ✅

Todas las claves (`SECRET_KEY`, `DB_PASSWORD`, `BREVO_API_KEY`, `SENTRY_DSN`)
vía variables de entorno (`python-decouple`, `config/settings/base.py` y
`prod.py`). `prod.py` valida que `SECRET_KEY` no sea un valor inseguro
("django-insecure", "change-me", etc.) y que tenga al menos 50 caracteres.

### 2. Eliminar secretos de Git — ✅

`.gitignore` ignora `.env`, `*.env`, `local_settings.py`. Nunca se commiteó
ningún `.env` (`git log --all -- .env` sin resultados). `detect-secrets`
corre como hook de pre-commit con `.secrets.baseline` — ver punto 28 (CI) para
el matiz de que este gate hoy es solo local.

### 3. Key pública para DB — N/A

Concepto de Supabase/Firebase (anon key vs. service key, cliente hablando
directo con la DB). Acá la arquitectura es Django tradicional: la DB de
Postgres nunca es accesible desde el cliente/mobile, todo pasa por la API con
JWT.

### 4. Row-Level Security — ✅ (vía patrón de aplicación, no RLS de Postgres)

No es RLS nativo de Postgres, pero hay un mecanismo sistemático equivalente:

- **Web**: `UserOwnedQuerysetMixin` (`apps/core/views.py`) filtra
  `.filter(user=self.request.user)` en `get_queryset()`. Todas las vistas de
  CRUD heredan de los `UserOwned*View` (`List/Create/Update/Delete/Detail`).
- **API**: cada `ViewSet` implementa `get_queryset()` filtrado por
  `user=self.request.user` individualmente — funciona, pero depende de que
  cada ViewSet nuevo lo haga bien a mano (no hay un mixin compartido del lado
  DRF).

### 5. Encriptar datos sensibles at-rest — ❌ (prioridad baja)

No hay campos encriptados a nivel de aplicación. No es información
ultra-sensible (gastos, montos, categorías — no tarjetas ni SSN), y
PostgreSQL de Render ya encripta at-rest a nivel de infraestructura. No se
considera deuda urgente.

### 6. Forzar autenticación — ✅

Todas las vistas de API declaran `permission_classes` explícitamente (ninguna
depende solo del default global, que es `AllowAny`). Web: todas las vistas de
CRUD heredan de `UserOwned*View` con `LoginRequiredMixin`.

**Nota de diseño a vigilar:** `DEFAULT_PERMISSION_CLASSES` es `AllowAny`
globalmente (`config/settings/base.py`). Si se agrega un ViewSet nuevo y se
olvida declarar `permission_classes`, queda abierto por defecto. No es un
hallazgo accionable hoy, pero conviene recordarlo al agregar endpoints nuevos.

### 7. Restringir acceso a registros (IDOR) — ✅

Mismo mecanismo que el punto 4: tanto `UserOwned*View` como los
`get_queryset()` filtrados devuelven 404 (no 403) si el recurso no es del
usuario — evita filtrar la existencia del recurso ajeno.

### 8. Bloquear manipulación de campos (mass assignment) — ✅

`read_only_fields` bien usados en los serializers DRF. El campo `user` nunca
está en `fields` de ningún serializer — se inyecta server-side en `create()`.
`ExpenseSerializer.validate_category()` verifica ownership de la categoría
enviada. `CategorySerializer` fuerza `is_system=False` al crear, ignorando lo
que mande el payload.

### 9. Proteger session cookies — ✅

`config/settings/prod.py`: `SESSION_COOKIE_SECURE=True`,
`CSRF_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`,
`CSRF_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE="Lax"`,
`CSRF_COOKIE_SAMESITE="Lax"`. Correctamente relajado en dev (HTTP local).

### 10. Hashear contraseñas — ✅

Sin `PASSWORD_HASHERS` sobreescrito en ningún settings — usa el default de
Django (PBKDF2SHA256).

### 11. Rate limiting — ✅ (DT-093, resuelto 2026-10-16)

`django-axes` ya protegía el login (web y, por transitividad, también el
login JWT de la API, porque `TokenObtainPairSerializer.validate()` pasa por
`AxesStandaloneBackend`). Faltaba cubrir registro y password-reset de la API:
`RegisterView`, `PasswordResetRequestView`, `PasswordResetConfirmView` ahora
usan `ScopedRateThrottle` (5 requests/hora por IP).

**Diferido, sin resolver:** las vistas web equivalentes (`RegisterView`,
`BrevoPasswordResetView` en `apps/users/views.py`) no tienen throttling —
`ScopedRateThrottle` es específico de DRF, no aplica a CBVs normales.
Requeriría `django-ratelimit` o un mecanismo propio con cache si se retoma.

### 12. Protección contra bots — ✅ (DT-095, resuelto 2026-10-16)

`HoneypotMixin` (`apps/core/forms.py`): campo trampa invisible, aplicado a
`RegisterForm` y `FeedbackForm`. Sin captcha ni dependencia externa — un bot
que completa todos los campos de un formulario cae en el honeypot; un usuario
real nunca lo ve.

### 13. Parametrizar queries — ✅

Sin SQL crudo en ningún lado (`grep` de `.raw(`, `.extra(`, `cursor.execute`,
`RawSQL` sin resultados). Todo el acceso a datos pasa por el ORM de Django.

### 14. Validar inputs — ✅

Buen ejemplo de defensa en profundidad real en `Expense`: `CheckConstraint`
a nivel de DB (`amount > 0`), validación de modelo en `clean()`, validación de
form (`apps/expenses/forms.py`, ownership de categoría), y
`validate_category()` en el serializer de API — las 4 capas replican la misma
regla.

### 15. Sanitizar contenido (XSS) — ✅

Sin `|safe` ni `mark_safe` en ningún template ni vista. Django templates
escapan por default y no se encontró ningún punto donde se rompa esa
protección.

### 16. Restringir archivos — ✅ (DT-094, resuelto 2026-10-16)

`ExpenseImportView` (único endpoint de upload del proyecto) validaba solo la
extensión del nombre del archivo. Ahora valida la firma real (magic bytes
`%PDF-`) antes de escribir a disco, y `DATA_UPLOAD_MAX_MEMORY_SIZE` /
`FILE_UPLOAD_MAX_MEMORY_SIZE` quedan declarados explícitamente en 5MB (antes
dependía del default implícito de Django).

### 17. Devolver datos necesarios — ✅

Ningún serializer expone `password`/hashes ni campos internos
(`is_superuser`, `is_staff`, `date_joined`) en los endpoints de perfil.

### 18. Security headers — ✅

CSP completo vía `django-csp` (sin `unsafe-inline`, con hash SHA256 para el
único script inline permitido), `X-Frame-Options: DENY`,
`SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY`,
`Permissions-Policy` (vía `PermissionsPolicyMiddleware` propio, desactiva
cámara/micrófono/geolocalización/pagos/etc.).

### 19. Forzar HTTPS — ✅

`SECURE_HSTS_SECONDS=31536000` (1 año), `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`,
`SECURE_HSTS_PRELOAD=True`, `SECURE_SSL_REDIRECT=True`. `SECURE_PROXY_SSL_HEADER`
configurado correctamente para el proxy de Render.

### 20. Escanear dependencias — ⚠️ (prioridad baja-media)

`pip-audit` y `safety` corren en el job `security` de `.github/workflows/ci.yml`,
pero con `continue-on-error: true` en ambos pasos — el pipeline no falla si
encuentran vulnerabilidades, solo las reporta. No hay Dependabot ni Renovate
configurados. Sugerencia: quitar `continue-on-error` o revisar el reporte
regularmente.

---

## Ronda 2 — Puntos ampliados

### 21. CSRF — ✅

`CsrfViewMiddleware` activo (`config/settings/base.py`, bien posicionado).
Sin ningún `@csrf_exempt` en todo el código. La API usa JWT en header
`Authorization: Bearer` (no cookies), así que no necesita CSRF — correcto por
diseño, no por exención explícita.

### 22. CORS restrictivo — ⚠️ (prioridad baja)

`django-cors-headers` instalado. `CORS_ALLOW_CREDENTIALS = True` global.
`config/settings/dev.py` tiene `CORS_ALLOW_ALL_ORIGINS = True` (comentado
como "solo en desarrollo") — es la combinación insegura (wildcard + credentials)
que vale la pena vigilar, pero está acotada a dev. En prod, `CORS_ALLOWED_ORIGINS`
queda vacío por default salvo que se configure explícitamente por variable de
entorno (no hay lectura de esa env var en `prod.py` hoy). Como Flutter mobile
no es un navegador, CORS no le aplica — solo sería relevante si en el futuro
JS del navegador necesitara llamar a `/api/v1/` desde otro origen.

**Sugerencia, si se retoma:** fijar `CORS_ALLOWED_ORIGINS` en `prod.py` desde
env var en vez de depender del default vacío por omisión, y documentar que es
intencional.

### 23. Autorización por roles (RBAC) — ✅ (N/A el concepto de roles propios)

No existe un sistema de roles más allá del `is_staff`/`is_superuser` nativo de
Django, usado solo para `/admin/`. No hay ninguna acción "de admin" expuesta
dentro de la app en sí: las categorías de sistema (`is_system=True`) solo se
crean vía migraciones/management command, nunca desde una vista HTTP, y los
endpoints de edición/borrado las excluyen explícitamente del queryset
editable. No hay huecos — simplemente no hace falta RBAC propio todavía.

### 24. MFA — ❌ (prioridad baja)

No implementado (confirmado: sin `django-otp`, `django-two-factor-auth` ni
nada custom, ni en código ni en dependencias). Aceptable para el tamaño
actual (app de finanzas personales individual). Candidato a revisar si crece
el volumen de usuarios reales.

### 25. Gestión de sesión y tokens — ⚠️ (prioridad media)

`SIMPLE_JWT`: access token 60 min, refresh token 30 días, con
`ROTATE_REFRESH_TOKENS=True` pero `BLACKLIST_AFTER_ROTATION=False` —
`rest_framework_simplejwt.token_blacklist` **no está instalado**. Esto
significa que **no hay forma de revocar un refresh token antes de que
expire** (hasta 30 días) — ni hay endpoint de logout para la API/mobile que
invalide el token (solo existen `TokenObtainPairView` y `TokenRefreshView`,
sin `TokenBlacklistView`). Si se pierde o roba un dispositivo con el token
guardado, queda válido hasta la expiración natural.

La sesión web sí es correcta: logout invalida la sesión de Django
correctamente (test explícito `test_logout_clears_session`).

**Camino de resolución:** instalar `rest_framework_simplejwt.token_blacklist`,
migrar, exponer un endpoint de logout que llame a
`RefreshToken(token).blacklist()`, y que el cliente mobile lo invoque al
cerrar sesión.

### 26. Recuperación de contraseña segura — ✅

Mensaje genérico sin enumeración de usuarios, confirmado tanto en la vista
web (`BrevoPasswordResetView`, comportamiento stock de Django) como en la API
(`"Si el email existe, vas a recibir un correo con instrucciones."`, con la
intención documentada en el código). El token expira: usa
`default_token_generator` sin `PASSWORD_RESET_TIMEOUT` sobreescrito, por lo
que aplica el default de Django (3 días).

### 27. Manejo de errores — ✅

`DEBUG=False` hardcodeado en `prod.py` (no leído de env var, con un guard
adicional que aborta el arranque si por algún motivo quedara en `True`).
`ALLOWED_HOSTS` vacío también aborta el arranque — no hay wildcard inseguro
de fallback. `templates/404.html`/`500.html` son genéricas, sin interpolar
tracebacks ni detalles internos. Sentry integrado con `send_default_pii=False`.

### 28. Logging y monitoreo — ✅

`apps/core/logging.py` cubre: intentos de login, logout, lockout (axes),
cambio de password, registro, permiso denegado, y acciones sensibles
genéricas (usado para eliminación de cuenta). Todos loguean solo
username/email + IP — ningún log interpola el valor de un password o token.

### 29. Backups cifrados y probados — ⚠️ (prioridad media)

`.github/workflows/backup.yml`: cron diario + disparo manual, `pg_dump -F c`
subido a Cloudflare R2 vía `rclone` (sobre HTTPS). Lo que el repo **no**
resuelve: el dump no se cifra con una clave propia del proyecto antes de
subirse (solo queda protegido por el cifrado at-rest que R2 aplique del lado
de Cloudflare, que es configuración de infraestructura, no de este código), y
no hay ningún restore-test automatizado que confirme periódicamente que el
backup realmente se puede restaurar.

### 30. Mínimo privilegio en infraestructura — ✅ en lo que el repo controla

`render.yaml` inyecta credenciales de DB vía referencia al recurso de Render
(`fromDatabase`, no hardcodeadas), y el resto de secretos usan `sync: false`
(se configuran manualmente en el dashboard, nunca se versionan). El resto
(permisos granulares del usuario de Postgres, políticas de buckets de R2) es
configuración de infraestructura fuera del alcance del repo.

### 31. Protección SSRF — ✅ (N/A, sin superficie de ataque)

Solo 2 puntos de red saliente en todo el código (Brevo para email, una API de
cotización de dólar), ambos con URL hardcodeada en el código — nunca viene de
input de usuario. Ningún endpoint acepta una URL externa para hacer fetch
server-side, y no hay webhooks entrantes.

### 32. Escaneo de secretos en CI — ❌ (prioridad media)

`detect-secrets` corre únicamente como hook de pre-commit **local** —
evitable con `git commit --no-verify`. El pipeline de CI no lo ejecuta en
ningún job.

**Camino de resolución:** agregar un step al job `security` de
`.github/workflows/ci.yml` que corra
`detect-secrets scan --baseline .secrets.baseline` (o `pre-commit run
detect-secrets --all-files`) y falle el build si detecta algo nuevo.

### 33. SAST/DAST — ❌ (prioridad media-baja)

No hay Semgrep, CodeQL, Bandit ni ningún escáner de seguridad estático o
dinámico configurado. `ruff` (ya en CI) es un linter de estilo, no detecta
patrones de seguridad como SQL injection o SSRF. Para el tamaño del proyecto
(desarrollador único, sin SQL crudo, ya auditado manualmente), el ROI es
menor que cerrar el punto 32, pero sigue siendo una brecha real. CodeQL vía
GitHub Advanced Security es gratis para repos públicos.

### 34. Auditoría de integraciones de terceros — ✅ (N/A, sin integraciones que lo requieran)

Brevo y Sentry se integran solo como clientes salientes (SDK/API), sin
ningún webhook entrante que requiera verificación de firma. No hay login
social ni OAuth de terceros implementado.

---

## Resumen de pendientes (ordenados por prioridad)

| # | Punto | Prioridad | Estado |
|---|---|---|---|
| 25 | Blacklist/logout real de JWT (refresh token no revocable) | Media | ❌ |
| 29 | Backup sin cifrado de capa de aplicación, sin restore-test | Media | ⚠️ |
| 32 | `detect-secrets` no corre en CI, solo local | Media | ❌ |
| 20 | `pip-audit`/`safety` en CI no bloquean el pipeline | Media-baja | ⚠️ |
| 33 | Sin SAST/DAST (Semgrep/CodeQL) | Media-baja | ❌ |
| 11 | Sin rate limiting en registro/password-reset **web** (solo API) | Baja | ⚠️ |
| 22 | CORS wildcard+credentials en dev (acotado, no afecta prod) | Baja | ⚠️ |
| 5 | Sin cifrado de datos sensibles at-rest a nivel de aplicación | Baja | ❌ |
| 24 | Sin MFA | Baja | ❌ |

Todo lo demás (25 de 34 puntos) está resuelto, correcto por diseño, o no
aplica a la arquitectura de esta app.
