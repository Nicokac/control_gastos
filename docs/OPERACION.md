# Operación — Control de Gastos

Cómo se despliega, se verifica, se vuelve atrás y se diagnostica la producción. La arquitectura está en [`ARQUITECTURA.md`](ARQUITECTURA.md); la app mobile y su release, en [`mobile/README.md`](../mobile/README.md).

Última revisión: 2026-11-10.

---

## Producción

| Item | Valor |
|---|---|
| Web | `https://controldegastos.ar` (también `https://control-gastos-fr8z.onrender.com`) |
| Servicio web | Render, plan **Free** (0,1 CPU, 512 MB). Se apaga tras 15 min sin tráfico |
| Base de datos | Render PostgreSQL, plan **Basic** (`basic-256mb`). No se apaga ni vence |
| Arranque | `gunicorn config.wsgi:application --workers 2 --timeout 60` |
| Build en Render | `pip install -r requirements/prod.txt && collectstatic && migrate` (ver `render.yaml`) |
| Healthcheck | `/healthz/` (verifica la conexión a la base) |
| Errores | Sentry (si `SENTRY_DSN` está cargado) |

El plan Free **no tiene Shell ni cron**: lo que en otro hosting se haría con un comando en el servidor se resuelve con un endpoint protegido llamado desde GitHub Actions (como los recordatorios push, D-019) o sumando el comando al build (como `ensure_superuser`).

---

## Deploy

Las migraciones corren solas en cada deploy (son parte del build).

### Checklist antes de pasar a `main`

```bash
pytest -q                                          # tests + coverage ≥ 80 %
ruff check . && ruff format --check .              # lint y formato
python manage.py makemigrations --check --dry-run  # sin migraciones pendientes
```

Chequeo de configuración de producción en local (PowerShell): `.\scripts\check_prod.ps1`.

### Deploy normal

Se trabaja en `develop` y se pasa a `main` con fast-forward:

```bash
git push origin develop && git checkout main && git pull --ff-only origin main && git merge --ff-only develop && git push origin main && git checkout develop
```

Push a `main` → **CI** (lint, tests, security, django-checks, build) → si pasa, **Deploy** llama al deploy hook de Render → Render construye y publica (~3-5 min). En paralelo, **Smoke Tests** espera 5 minutos y prueba `/healthz/`, `/`, `/users/login/`, `/users/register/`, `/terms/` y `/privacy/`.

GitHub muestra "Bypassed rule violations" al pushear a `main` sin PR: es esperado.

### Deploy manual

Render → servicio → **Manual Deploy** → *Deploy latest commit* (o un commit puntual). También: GitHub → Actions → Deploy → *Run workflow*.

### Verificación

```bash
curl https://controldegastos.ar/healthz/   # "ok"
curl -I https://controldegastos.ar/        # 200
```

Y en el navegador, con **Ctrl+F5** (los JS y CSS llevan `?v=APP_VERSION`, pero conviene descartar caché): versión en el sidebar y el cambio que se subió.

---

## Rollback

| Opción | Cuándo | Cómo |
|---|---|---|
| Render | Lo más rápido (~2 min) | Servicio → Events → deploy anterior → *Rollback to this deploy* |
| `git revert` | Para dejar el historial coherente | `git revert <commit>` en `develop`, pasar a `main` como un deploy normal |

**Ojo con las migraciones:** el rollback de Render vuelve el código, no la base. Si el deploy problemático incluía una migración que cambia o borra columnas, el código viejo puede no funcionar con el esquema nuevo. En ese caso, preferir un fix hacia adelante o restaurar el backup.

---

## Variables de entorno

Se cargan en Render → servicio → **Environment**. Ejemplos y defaults en [`.env.example`](../.env.example).

> Al cambiar una variable, usar **Save and deploy**. Con *Save only* el servicio sigue con el valor anterior hasta el próximo deploy.

| Variable | Requerida | Para qué |
|---|---|---|
| `SECRET_KEY` | Sí | Django. Generar con `python manage.py generate_secret_key` |
| `DJANGO_SETTINGS_MODULE` | Sí | `config.settings.prod` |
| `DEBUG` | Sí | `False` |
| `ALLOWED_HOSTS` | Sí | Hosts separados por coma, sin `https://`. `CSRF_TRUSTED_ORIGINS` se arma desde acá |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Sí | Vienen de la base de Render (`render.yaml`) |
| `BREVO_API_KEY` | Sí | Envío de todos los emails |
| `BREVO_SENDER_EMAIL`, `CONTACT_EMAIL`, `SITE_URL` | No | Remitente, Reply-To y dominio de los links. Defaults en `controldegastos.ar` |
| `CRON_SECRET` | Sí | Protege el endpoint del cron diario. El mismo valor va en GitHub |
| `FIREBASE_CREDENTIALS_PATH` | Sí (push) | Ruta al JSON de la service account de Firebase, cargado como Secret File en Render (`/etc/secrets/`). Vacía = no se envían push |
| `SENTRY_DSN` | No | Errores en Sentry |
| `ADMIN_EMAIL`, `FEEDBACK_EMAIL`, `SERVER_EMAIL` | No | Destinatarios de errores y del formulario de feedback |

### Secrets de GitHub Actions

| Secret | Lo usa |
|---|---|
| `RENDER_DEPLOY_HOOK` | Deploy |
| `PRODUCTION_URL` | Smoke Tests y Recordatorios push |
| `CRON_SECRET` | Recordatorios push |
| `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Backup DB (host externo de la base) |
| `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `CF_ACCOUNT_ID` | Backup DB |

---

## Tareas programadas

| Workflow | Horario | Qué hace | Cómo verificar |
|---|---|---|---|
| Recordatorios push (`reminders.yml`) | 12:00 UTC (09:00 AR) | Avisos de gastos fijos que vencen en 3 días o vencieron ayer, y chequeo de la key de Brevo | El log del job muestra `{"sent": N, "brevo_ok": true}` |
| Backup DB (`backup.yml`) | 03:00 UTC (00:00 AR) | `pg_dump` de producción a Cloudflare R2 | Job en verde y archivo nuevo en el bucket |

Los dos se pueden correr a mano: Actions → workflow → *Run workflow*.

---

## Backups

- **Automático:** `backup.yml`, diario, a Cloudflare R2.
- **Manual desde la PC (PowerShell):** `.\scripts\backup_db.ps1`.
- **Restaurar:** `.\scripts\restore_db.ps1 <archivo.dump>`. Restaurar sobre producción pisa los datos actuales: hacer antes un backup manual.

---

## Tareas de administración sin Shell

| Necesidad | Cómo |
|---|---|
| Crear o recuperar el superusuario | Comando `ensure_superuser`, que lee `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD`. No está en el build: cargar esas variables, sumar `&& python manage.py ensure_superuser` al *Build Command* de Render, deployar, y después sacar el comando y las variables |
| Ver errores | Sentry, o Render → servicio → **Logs** |
| Usuario bloqueado por intentos fallidos (axes, 5 intentos, 2 h) | Esperar el cooloff, o desde el admin de Django (`/admin/` → Axes → Access attempts) borrar sus intentos |
| Probar un push a un usuario | En local con credenciales de Firebase: `python manage.py send_test_push` |
| Correr los recordatorios fuera de horario | Actions → Recordatorios push → *Run workflow* |

Comandos de gestión del proyecto (en local): `seed_categories`, `generate_secret_key`, `axes_status`, `view_logs`, `ensure_superuser`, `send_recurring_reminders`, `send_test_push`.

---

## Problemas comunes

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| El primer pedido tarda mucho | Arranque en frío de Render Free | Esperado. Opciones y costos en DT-106 |
| `DisallowedHost` / `Invalid HTTP_HOST header` | El dominio no está en `ALLOWED_HOSTS` | Agregarlo (sin `https://`) y redeployar |
| `CSRF verification failed` | Ídem: `CSRF_TRUSTED_ORIGINS` sale de `ALLOWED_HOSTS` | Revisar `ALLOWED_HOSTS` |
| `OperationalError: could not connect` | Variables `DB_*` mal o base caída | Revisar la base en Render; el servicio usa el host interno |
| No llegan emails | Key de Brevo desactivada, o el destinatario tocó "Darse de baja" | Sentry muestra el motivo (DT-108). Brevo → E-mails transaccionales → Contactos bloqueados |
| `"brevo_ok": false` en el cron | La key de Brevo no funciona | Generar una nueva y cargarla en Render con *Save and deploy* |
| No llegan push | Falta `FIREBASE_CREDENTIALS_PATH`, el usuario los desactivó o el token está inactivo | Revisar el log del cron y la tabla `DeviceToken` en el admin |
| El navegador muestra la versión vieja | Caché | Ctrl+F5 |

---

## Monitoreo

| Qué | Dónde |
|---|---|
| Servicio arriba | `/healthz/` |
| Errores | Sentry |
| Logs | Render → servicio → Logs |
| CI, deploys, cron y backups | GitHub → Actions |
| Emails enviados y rebotes | Brevo → E-mails transaccionales → Registros |
