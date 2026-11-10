# Arquitectura — Control de Gastos

Cómo está armado el sistema: qué piezas hay, cómo se hablan y dónde corre cada una. El *porqué* de cada decisión está en [`DECISIONS.md`](DECISIONS.md); acá se enlaza la entrada correspondiente.

Última revisión: 2026-11-10 (web 1.29.6, mobile 1.27.2+37).

> **Ver los diagramas:** GitHub los muestra directamente. En VS Code hace falta la extensión *Markdown Preview Mermaid Support*. El diagrama de base de datos está en [`database.dbml`](database.dbml): se pega en [dbdiagram.io](https://dbdiagram.io/d).

---

## Índice

1. [Vista general](#1-vista-general)
2. [Componentes](#2-componentes)
3. [Backend Django](#3-backend-django)
4. [App mobile Flutter](#4-app-mobile-flutter)
5. [Flujos principales](#5-flujos-principales)
6. [Modelo de datos](#6-modelo-de-datos)
7. [CI/CD y tareas programadas](#7-cicd-y-tareas-programadas)
8. [Entornos y configuración](#8-entornos-y-configuración)
9. [Seguridad](#9-seguridad)
10. [Limitaciones conocidas](#10-limitaciones-conocidas)

---

## 1. Vista general

Un único backend Django sirve dos clientes: la **web** (templates HTML con sesión) y la **app Android** (API REST con JWT). Todo corre en Render; los servicios externos se usan por API HTTP.

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Segoe UI, Roboto, sans-serif", "fontSize": "14px", "lineColor": "#6c757d", "primaryTextColor": "#212529", "clusterBkg": "#f8f9fa", "clusterBorder": "#dee2e6"}}}%%
flowchart LR
    subgraph clientes["Clientes"]
        web["🖥️ Navegador<br/><small>Web HTML + Bootstrap</small>"]
        app["📱 App Android<br/><small>Flutter</small>"]
    end

    subgraph cloudflare["Cloudflare"]
        dns["DNS<br/><small>controldegastos.ar</small>"]
        mailroute["Email Routing<br/><small>contacto@</small>"]
    end

    subgraph render["Render"]
        django["⚙️ Django 5.2 + DRF<br/><small>gunicorn · plan Free</small>"]
        db[("🐘 PostgreSQL<br/><small>plan Basic</small>")]
    end

    subgraph externos["Servicios externos"]
        brevo["✉️ Brevo<br/><small>email transaccional</small>"]
        fcm["🔔 Firebase<br/><small>Cloud Messaging</small>"]
        dolar["💵 dolarapi.com<br/><small>cotización oficial</small>"]
        sentry["🐞 Sentry<br/><small>errores</small>"]
    end

    subgraph github["GitHub"]
        actions["⏱️ Actions<br/><small>CI · deploy · cron · backup</small>"]
    end

    r2[("☁️ Cloudflare R2<br/><small>backups</small>")]

    web -- "HTTPS · sesión" --> dns
    dns --> django
    app -- "HTTPS · JWT<br/>/api/v1/" --> django
    django --> db
    django -- "API HTTP" --> brevo
    django -- "firebase-admin" --> fcm
    fcm -. "push" .-> app
    django -- "cache 1 h" --> dolar
    django -. "eventos" .-> sentry
    actions -- "deploy hook · cron" --> django
    actions -- "pg_dump" --> db
    actions --> r2
    brevo -. "mails" .-> usuarios(("👤 Usuario"))
    usuarios -. "respuestas" .-> mailroute

    classDef client fill:#e7f1ff,stroke:#0d6efd,stroke-width:2px,color:#052c65
    classDef core fill:#d1e7dd,stroke:#198754,stroke-width:2px,color:#0a3622
    classDef data fill:#fff3cd,stroke:#ffc107,stroke-width:2px,color:#664d03
    classDef ext fill:#f8d7da,stroke:#dc3545,stroke-width:1px,color:#58151c
    classDef ops fill:#e2e3e5,stroke:#6c757d,stroke-width:1px,color:#2b2f32
    classDef cf fill:#ffe5d0,stroke:#fd7e14,stroke-width:1px,color:#653208

    class web,app client
    class django core
    class db,r2 data
    class brevo,fcm,dolar,sentry ext
    class actions ops
    class dns,mailroute cf
```

| Dato | Valor |
|---|---|
| Web | `https://controldegastos.ar` (también `control-gastos-fr8z.onrender.com`) |
| API | `https://control-gastos-fr8z.onrender.com/api/v1/` (la app todavía usa la URL de Render, D-020) |
| Documentación de la API | `/api/v1/docs/` (Swagger, generado por drf-spectacular) |
| Zona horaria | `America/Argentina/Buenos_Aires` (D-012) |

---

## 2. Componentes

| Componente | Tecnología | Dónde corre | Para qué | Referencia |
|---|---|---|---|---|
| Backend | Django 5.2, DRF, SimpleJWT | Render (web service Free) | Web HTML, API REST, reglas de negocio | D-017 |
| Base de datos | PostgreSQL (prod) / SQLite (dev y tests) | Render (Basic) | Persistencia | D-017 |
| App mobile | Flutter, Riverpod, Dio, GoRouter | Android (Google Play) | Cliente nativo de la API | `FLUTTER_ROADMAP.md` |
| DNS | Cloudflare (plan Free, "DNS only") | — | Dominio `controldegastos.ar` | D-020 |
| Email saliente | Brevo (API HTTP, sin SMTP) | — | Reset de contraseña, verificación, bienvenida, feedback | D-013, DT-108 |
| Email entrante | Cloudflare Email Routing | — | `contacto@` reenvía a la casilla del proyecto | D-020 |
| Push | Firebase Cloud Messaging | — | Recordatorios y alertas de gasto | D-019 |
| Cotización | dolarapi.com | — | Dólar oficial para cargar gastos en USD | — |
| Errores | Sentry | — | Excepciones y logs de error en producción | — |
| CI/CD y cron | GitHub Actions | GitHub | Tests, deploy, recordatorios diarios, backups | — |
| Backups | Cloudflare R2 | — | `pg_dump` diario | — |

---

## 3. Backend Django

### Apps

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Segoe UI, Roboto, sans-serif", "fontSize": "13px", "lineColor": "#adb5bd"}}}%%
flowchart TB
    subgraph entrada["Entrada"]
        templates["Vistas HTML<br/><small>views.py de cada app</small>"]
        api["api/v1<br/><small>ViewSets DRF + JWT</small>"]
    end

    subgraph dominio["Dominio"]
        expenses["expenses"]
        income["income"]
        recurring["recurring"]
        recurring_income["recurring_income"]
        savings["savings"]
        shared["shared_expenses"]
        categories["categories"]
        reports["reports<br/><small>dashboard y métricas</small>"]
        notifications["notifications<br/><small>push, recordatorios, alertas</small>"]
    end

    subgraph base["Base"]
        users["users<br/><small>User propio, auth</small>"]
        core["core<br/><small>mixins, utils, Brevo, versión</small>"]
    end

    templates --> dominio
    api --> dominio
    dominio --> base
    expenses -. "post_save" .-> notifications
    notifications --> recurring

    classDef entry fill:#e7f1ff,stroke:#0d6efd,color:#052c65
    classDef domain fill:#d1e7dd,stroke:#198754,color:#0a3622
    classDef basecls fill:#e2e3e5,stroke:#6c757d,color:#2b2f32
    class templates,api entry
    class expenses,income,recurring,recurring_income,savings,shared,categories,reports,notifications domain
    class users,core basecls
```

| App | Responsabilidad |
|---|---|
| `core` | Mixins comunes (`TimeStampedModel`, multimoneda con `amount_ars`), envío por Brevo (`send_brevo_email`, `check_brevo_account`), cotización del dólar, `APP_VERSION` y `WHATS_NEW` |
| `users` | Modelo `User` propio, login por email o usuario, verificación de email, reset de contraseña, preferencias |
| `categories` | Categorías de sistema y propias, jerarquía grupo → subcategoría (D-011), ocultar categorías de sistema |
| `expenses`, `income` | Movimientos en ARS o USD; importación de resúmenes de tarjeta (beta) |
| `recurring`, `recurring_income` | Gastos fijos (con cuotas y débito automático) e ingresos fijos |
| `savings` | Metas de ahorro, depósitos y retiros, sugerencia de pasar el sobrante del mes a una meta |
| `shared_expenses` | Gastos del hogar con miembros sin cuenta (D-018) |
| `reports` | Dashboard web, evolución mensual, proyección al cierre |
| `notifications` | Tokens de dispositivo, envío push, recordatorios de vencimiento, alertas por umbral, historial |
| `api` | API REST v1 para la app mobile |
| `budgets` | Sin modelos: el módulo se eliminó (D-007) |

### Convenciones que conviene conocer

- **Multimoneda:** cada movimiento guarda `amount`, `currency`, `exchange_rate` y `amount_ars`. Las métricas siempre suman `amount_ars`, que se calcula en Python al guardar (D-001).
- **Mes financiero:** el usuario elige el día en que arranca su mes (`financial_month_start_day`); los períodos del dashboard y las alertas lo respetan.
- **Fechas:** se usa `timezone.localdate()` y no `now().date()` (D-012).
- **Aislamiento por usuario:** todas las consultas filtran por `request.user`; las vistas usan mixins de `core` para no repetirlo.
- **Caché:** `LocMemCache` en memoria del proceso (cotización del dólar, rate limiting de `/healthz/`). Se pierde en cada reinicio.

---

## 4. App mobile Flutter

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Segoe UI, Roboto, sans-serif", "fontSize": "13px", "lineColor": "#adb5bd"}}}%%
flowchart LR
    ui["features/*<br/><small>screens y widgets</small>"] --> prov["Providers<br/><small>Riverpod</small>"]
    prov --> repo["data/repositories<br/><small>uno por recurso</small>"]
    repo --> apisvc["ApiService<br/><small>Dio + interceptores</small>"]
    repo --> cache["CacheService<br/><small>shared_preferences</small>"]
    apisvc --> storage["StorageService<br/><small>flutter_secure_storage</small>"]
    apisvc -- "HTTPS JWT" --> backend(("API<br/>Django"))
    push["PushNotificationService<br/><small>firebase_messaging</small>"] --> repo

    classDef uiCls fill:#e7f1ff,stroke:#0d6efd,color:#052c65
    classDef logic fill:#d1e7dd,stroke:#198754,color:#0a3622
    classDef infra fill:#fff3cd,stroke:#ffc107,color:#664d03
    class ui uiCls
    class prov,repo,push logic
    class apisvc,cache,storage infra
```

| Carpeta | Contenido |
|---|---|
| `lib/features/` | Una carpeta por sección (auth, dashboard, expenses, income, recurring, savings, shared_expenses, categories, notifications, settings, feedback) con sus pantallas, providers y widgets |
| `lib/data/repositories/` | Acceso a la API por recurso |
| `lib/data/services/` | `ApiService` (Dio), `StorageService` (tokens en almacenamiento seguro), `CacheService` (última respuesta en `shared_preferences` para mostrar algo sin conexión), `PushNotificationService` |
| `lib/core/` | Constantes (`api_constants.dart`: URL de la API, links, resumen de la última versión), tema, formateadores de montos, widgets comunes |
| `lib/routing/` | Rutas con GoRouter |

- **URL de la API:** `--dart-define=API_BASE_URL=...`; por defecto, producción. Para el emulador contra el servidor local: `http://10.0.2.2:8001/api/v1`.
- **Versión:** `pubspec.yaml` (`X.Y.Z+N`); el número de build sube en cada subida a Play Console.

---

## 5. Flujos principales

### 5.1 Login y renovación del token (mobile)

Access token de 60 minutos y refresh de 30 días, con rotación. La app renueva sola cuando recibe un 401.

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Segoe UI, Roboto, sans-serif", "actorBkg": "#e7f1ff", "actorBorder": "#0d6efd", "actorTextColor": "#052c65", "signalColor": "#495057", "noteBkgColor": "#fff3cd", "noteBorderColor": "#ffc107", "activationBkgColor": "#d1e7dd", "activationBorderColor": "#198754"}}}%%
sequenceDiagram
    autonumber
    participant App as 📱 App
    participant Store as Almacenamiento seguro
    participant API as ⚙️ API Django

    App->>API: POST /auth/token/ (email o usuario + contraseña)
    API-->>App: access (60 min) + refresh (30 días)
    App->>Store: guarda los dos tokens
    App->>API: GET /dashboard/ (Bearer access)
    API-->>App: 200 datos

    Note over App,API: Más tarde, el access vence
    App->>API: GET /expenses/ (access vencido)
    API-->>App: 401
    activate App
    App->>Store: lee refresh
    App->>API: POST /auth/token/refresh/
    API-->>App: access nuevo + refresh nuevo (rotación)
    App->>Store: guarda los tokens nuevos
    App->>API: reintenta GET /expenses/
    deactivate App
    API-->>App: 200
    Note over App: Si el refresh también falló, vuelve al login
```

La web usa sesión de Django (cookie de 14 días) con `django-axes`: 5 intentos fallidos bloquean la cuenta.

### 5.2 Notificaciones push

Dos disparadores: el **cron diario** (vencimientos de gastos fijos) y el **guardado de un gasto** (alertas por umbral). Los logs (`RecurringReminderLog`, `SpendingAlertLog`) garantizan un solo aviso por vencimiento o por período.

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Segoe UI, Roboto, sans-serif", "actorBkg": "#e7f1ff", "actorBorder": "#0d6efd", "actorTextColor": "#052c65", "signalColor": "#495057", "noteBkgColor": "#fff3cd", "noteBorderColor": "#ffc107"}}}%%
sequenceDiagram
    autonumber
    participant App as 📱 App
    participant API as ⚙️ Django
    participant DB as 🐘 PostgreSQL
    participant FCM as 🔔 Firebase
    participant GH as ⏱️ GitHub Actions

    rect rgb(231, 241, 255)
    Note over App,FCM: Registro (al iniciar sesión o abrir la app)
    App->>FCM: obtiene el Installation ID (FID)
    App->>API: POST /notifications/device-token/
    API->>DB: DeviceToken (activo)
    end

    rect rgb(209, 231, 221)
    Note over GH,FCM: Recordatorios: todos los días 12:00 UTC
    GH->>API: POST /notifications/cron/recurring-reminders/ (X-Cron-Secret)
    API->>DB: gastos fijos que vencen en 3 días o vencieron ayer sin pago
    API->>DB: RecurringReminderLog (evita repetidos) + Notification
    API->>FCM: send_each_for_multicast(fids)
    FCM-->>App: push
    API->>API: check_brevo_account() (DT-108)
    API-->>GH: {"sent": n, "brevo_ok": true}
    end

    rect rgb(255, 243, 205)
    Note over App,FCM: Alertas de gasto: al guardar un gasto
    App->>API: POST /expenses/
    API->>DB: guarda el gasto
    API->>API: post_save → on_commit → check_spending_alerts
    API->>DB: ¿superó el umbral global o el de la subcategoría en el período?
    API->>DB: SpendingAlertLog + Notification
    API->>FCM: push
    end

    Note over App,API: Al cerrar sesión: DELETE /notifications/device-token/ desactiva el token
```

### 5.3 Email transaccional

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Segoe UI, Roboto, sans-serif", "lineColor": "#6c757d"}}}%%
flowchart LR
    trigger["Reset de contraseña<br/>Verificación de email<br/>Bienvenida · Feedback"] --> send["core.utils<br/>send_brevo_email()"]
    send -- "POST /v3/smtp/email" --> brevo["✉️ Brevo"]
    brevo -- "From: noreply@controldegastos.ar<br/>DKIM + DMARC" --> inbox(("👤 Bandeja"))
    inbox -- "Responder<br/>(Reply-To)" --> cf["Cloudflare Email Routing<br/>contacto@controldegastos.ar"]
    cf --> gmail["Casilla del proyecto"]
    send -. "si falla: log con motivo" .-> sentry["🐞 Sentry"]

    classDef ext fill:#f8d7da,stroke:#dc3545,color:#58151c
    classDef core fill:#d1e7dd,stroke:#198754,color:#0a3622
    classDef cfc fill:#ffe5d0,stroke:#fd7e14,color:#653208
    class brevo,sentry ext
    class trigger,send core
    class cf,gmail cfc
```

Sin SMTP: todo sale por la API HTTP de Brevo. El reset de contraseña de la web pasa por `BrevoPasswordResetForm` (DT-082).

### 5.4 Carga de un gasto en dólares (web)

1. El formulario pide la cotización a `/api/exchange-rate/` (vista de `core`), que consulta dolarapi.com y la guarda en caché una hora.
2. El usuario confirma o corrige la cotización.
3. Al guardar, el modelo calcula `amount_ars = amount × exchange_rate` (D-001).
4. `post_save` dispara las alertas de gasto (5.2).

---

## 6. Modelo de datos

El esquema completo, con tipos, restricciones y notas, está en **[`database.dbml`](database.dbml)**. Para verlo como diagrama, pegar el archivo en [dbdiagram.io](https://dbdiagram.io/d); las tablas aparecen coloreadas por grupo.

Resumen de las relaciones:

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Segoe UI, Roboto, sans-serif", "primaryColor": "#e7f1ff", "primaryBorderColor": "#0d6efd", "lineColor": "#6c757d", "tertiaryColor": "#f8f9fa"}}}%%
erDiagram
    USER ||--o{ CATEGORY : "crea (las de sistema no tienen user)"
    CATEGORY ||--o{ CATEGORY : "grupo → subcategoría"
    USER ||--o{ EXPENSE : registra
    USER ||--o{ INCOME : registra
    CATEGORY ||--o{ EXPENSE : clasifica
    CATEGORY ||--o{ INCOME : clasifica
    USER ||--o{ RECURRING_EXPENSE : define
    RECURRING_EXPENSE |o--o{ EXPENSE : "se paga con"
    USER ||--o{ RECURRING_INCOME : define
    RECURRING_INCOME |o--o{ INCOME : "se cobra con"
    USER ||--o{ SAVING : tiene
    SAVING ||--o{ SAVING_MOVEMENT : "depósitos y retiros"
    SAVING |o--o{ EXPENSE : "gasto vinculado"
    USER ||--o{ ROLLOVER_SUGGESTION : recibe
    USER ||--o{ HOUSEHOLD_MEMBER : "miembros del hogar"
    HOUSEHOLD_MEMBER |o--o{ SHARED_EXPENSE : paga
    USER ||--o{ SHARED_EXPENSE : registra
    USER ||--o{ DEVICE_TOKEN : "dispositivos"
    USER ||--o{ NOTIFICATION : "historial"
    RECURRING_EXPENSE ||--o{ RECURRING_REMINDER_LOG : "avisos enviados"
    USER ||--o{ SPENDING_ALERT_LOG : "alertas enviadas"
```

---

## 7. CI/CD y tareas programadas

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Segoe UI, Roboto, sans-serif", "lineColor": "#6c757d", "clusterBkg": "#f8f9fa", "clusterBorder": "#dee2e6"}}}%%
flowchart LR
    dev["💻 develop"] -- "push" --> ci1["CI<br/><small>lint · tests · security</small>"]
    dev -- "merge fast-forward" --> main["🌿 main"]
    main -- "push" --> ci2["CI"]
    ci2 -- "ok" --> deploy["Deploy<br/><small>deploy hook</small>"]
    deploy --> render["⚙️ Render<br/><small>pip · collectstatic · migrate</small>"]
    render -- "/healthz/" --> live(("🟢 En línea"))
    main -- "push" --> smoke["Smoke tests<br/><small>espera 5 min</small>"]
    smoke -.-> live

    subgraph cron["Programados"]
        rem["Recordatorios push<br/><small>12:00 UTC</small>"]
        bak["Backup DB → R2<br/><small>03:00 UTC</small>"]
    end
    rem --> render
    bak --> r2[("☁️ R2")]

    classDef branch fill:#e7f1ff,stroke:#0d6efd,color:#052c65
    classDef job fill:#e2e3e5,stroke:#6c757d,color:#2b2f32
    classDef prod fill:#d1e7dd,stroke:#198754,color:#0a3622
    class dev,main branch
    class ci1,ci2,deploy,smoke,rem,bak job
    class render,live prod
```

| Workflow | Disparo | Qué hace |
|---|---|---|
| `ci.yml` | push o PR a `develop` / `main` | Ruff (lint y formato), pytest con coverage ≥ 80 %, chequeos de seguridad |
| `deploy.yml` | CI exitoso en `main` | Llama al deploy hook de Render |
| `smoke.yml` | push a `main` | Espera el deploy y prueba endpoints clave |
| `reminders.yml` | diario 12:00 UTC | Recordatorios push + chequeo de la key de Brevo |
| `backup.yml` | diario 03:00 UTC | `pg_dump` de producción a Cloudflare R2 |

Flujo de ramas: se trabaja en `develop` y se pasa a `main` con fast-forward. El build de la app mobile se hace a mano y se sube a Play Console.

---

## 8. Entornos y configuración

| | Desarrollo | Tests | Producción |
|---|---|---|---|
| Settings | `config.settings.dev` | `config.settings.dev` | `config.settings.prod` |
| Base de datos | SQLite | SQLite | PostgreSQL (Render) |
| Email | Brevo si hay `BREVO_API_KEY`; si no, consola | Brevo mockeado; el fallback va a `mailoutbox` | Brevo |
| Push | Sin `FIREBASE_CREDENTIALS_PATH`: no envía | Firebase mockeado | Firebase (service account) |
| Servidor | `runserver` (puerto 8001 para el emulador) | — | gunicorn, 2 workers |

Las variables de entorno están documentadas en [`.env.example`](../.env.example). En producción se cargan en Render; al cambiarlas hay que redeployar.

**Diferencias SQLite / PostgreSQL:** las funciones de fecha y las agregaciones no se comportan igual. Toda lógica que agrupa por día, mes o período tiene tests, pero los tests corren en SQLite.

---

## 9. Seguridad

| Capa | Medida | Referencia |
|---|---|---|
| Login web | `django-axes`: 5 intentos fallidos bloquean | — |
| API | JWT con rotación de refresh; throttling de DRF | — |
| Cabeceras | CSP sin `unsafe-inline` en scripts; scripts de CDN con versión fija y SRI | D-009 |
| `/healthz/` | Rate limiting por IP en memoria | D-004, D-005 |
| Cron | Endpoint protegido con `X-Cron-Secret` (comparación en tiempo constante) | D-019 |
| Datos | Cada consulta filtra por el usuario logueado | — |
| Secretos | Solo en variables de entorno de Render y secrets de GitHub | — |

Auditoría completa en [`AUDITORIA_SEGURIDAD.md`](AUDITORIA_SEGURIDAD.md).

---

## 10. Limitaciones conocidas

| Limitación | Impacto | Referencia |
|---|---|---|
| Render Free apaga el servicio tras 15 min sin tráfico | El primer pedido tarda en despertarlo | DT-106 |
| Caché en memoria del proceso | Con 2 workers cada uno tiene su caché; se pierde al reiniciar | — |
| La app mobile usa la URL de Render para la API | Cambiar de hosting obliga a publicar una versión nueva | D-020 |
| Brevo agrega "Darse de baja" a los mails transaccionales | Si un usuario lo toca, deja de recibir el reset de contraseña | — |
| Interfaz solo en español | Barrera para usuarios fuera de Argentina | DT-105 |
