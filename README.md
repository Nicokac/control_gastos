#
 Control de Gastos

Aplicación web para el control y seguimiento de finanzas personales desarrollada con Django.
##
 Descripción

Control de Gastos permite a los usuarios:
-
 Registrar gastos e ingresos con soporte multimoneda (ARS/USD)
-
 Categorizar transacciones con categorías predefinidas y personalizadas
-
 Registrar aportes a ahorro/inversión
-
 Establecer presupuestos mensuales (globales o por categoría)
-
 Visualizar dashboards con gráficos de distribución y tendencias
-
 Recibir alertas visuales cuando se acercan a los límites de presupuesto
-
 Exportar datos a CSV y Excel
##
 Stack Tecnológico

-
 
**
Backend:
**
 Python 3.11+ / Django 5.x
-
 
**
Frontend:
**
 Django Templates + Bootstrap 5
-
 
**
Base de datos:
**
 SQLite (desarrollo) / PostgreSQL (producción)
-
 
**
Gráficos:
**
 Chart.js
##
 Requisitos Previos

-
 Python 3.11 o superior
-
 pip
-
 Git
##
 Instalación

###
 1. Clonar el repositorio

```
bash

git
 clone https://github.com/TU_USUARIO/control_gastos.git
cd
 control_gastos

```

###
 2. Crear y activar entorno virtual

**
Windows (PowerShell):
**

```
powershell

python 
-
m venv venv
.
\venv\Scripts\Activate
.
ps1

```

**
Linux/Mac:
**

```
bash

python3 -m venv venv
source
 venv/bin/activate

```

###
 3. Instalar dependencias

```
bash

pip 
install
 -r requirements/dev.txt

```

###
 4. Configurar variables de entorno

Crear archivo 
`.env`
 en la raíz del proyecto:
```
env

SECRET_KEY=tu-clave-secreta-aqui
DJANGO_SETTINGS_MODULE=config.settings.dev

```

###
 5. Aplicar migraciones

```
bash

python manage.py migrate

```

###
 6. Crear superusuario

```
bash

python manage.py createsuperuser

```

###
 7. Ejecutar servidor de desarrollo

```
bash

python manage.py runserver

```

Acceder a http://127.0.0.1:8000
##
 Estructura del Proyecto

```

control_gastos/
├── apps/                   # Aplicaciones Django
│   ├── budgets/           # Presupuestos y alertas
│   ├── categories/        # Gestión de categorías
│   ├── core/              # Utilidades compartidas
│   ├── expenses/          # Registro de gastos
│   ├── income/            # Registro de ingresos
│   ├── reports/           # Dashboard y visualizaciones
│   ├── savings/           # Ahorro e inversiones
│   └── users/             # Autenticación y perfiles
├── config/                # Configuración del proyecto
│   └── settings/          # Settings por entorno
├── static/                # Archivos estáticos
├── templates/             # Templates HTML
├── requirements/          # Dependencias por entorno
└── manage.py

```

##
 Apps y Funcionalidades

|
 App 
|
 Descripción 
|

|
-----
|
-------------
|

|
 
`users`
 
|
 Autenticación, registro y preferencias de usuario 
|

|
 
`categories`
 
|
 CRUD de categorías (sistema + personalizadas) 
|

|
 
`expenses`
 
|
 Registro y gestión de gastos 
|

|
 
`income`
 
|
 Registro de ingresos 
|

|
 
`savings`
 
|
 Registro de ahorro/inversión 
|

|
 
`budgets`
 
|
 Presupuestos mensuales con alertas 
|

|
 
`reports`
 
|
 Dashboard, gráficos y exportación 
|

|
 
`core`
 
|
 Mixins, constantes y utilidades 
|


##
 Configuración por Entorno

-
 
`config/settings/base.py`
 - Configuración común
-
 
`config/settings/dev.py`
 - Desarrollo (DEBUG=True, SQLite)
-
 
`config/settings/prod.py`
 - Producción (DEBUG=False, PostgreSQL)
##
 Comandos Útiles

```
bash

# Crear migraciones

python manage.py makemigrations
# Aplicar migraciones

python manage.py migrate
# Ejecutar tests

python manage.py 
test

# Formatear código

black 
.

# Lint

flake8

```

##
 Flujo de Git

-
 
`main`
 - Código estable, listo para producción
-
 
`develop`
 - Integración de features
-
 
`feature/*`
 
-
 Desarrollo de nuevas funcionalidades
-
 
`fix/*`
 - Corrección de bugs
###
 Formato de commits

Seguimos 
[
Conventional Commits
](
https://www.conventionalcommits.org/
)
:
```

feat(expenses): add expense creation form
fix(budgets): correct alert threshold calculation
docs(readme): update installation instructions

```

##
 Roadmap MVP

-
 [x] Scaffolding del proyecto
-
 [ ] Implementación de modelos
-
 [ ] Sistema de autenticación
-
 [ ] CRUD de categorías
-
 [ ] CRUD de gastos
-
 [ ] CRUD de ingresos
-
 [ ] CRUD de ahorro/inversión
-
 [ ] Sistema de presupuestos y alertas
-
 [ ] Dashboard con gráficos
-
 [ ] Exportación CSV/Excel
##
 Licencia

Este proyecto es de uso privado.
##
 Autor

Nicolás Kachuk
