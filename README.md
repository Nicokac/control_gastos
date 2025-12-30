# Control de Gastos

Aplicación web para el control y seguimiento de finanzas personales desarrollada con Django.

## Descripción

Control de Gastos permite a los usuarios:

- Registrar gastos e ingresos con soporte multimoneda (ARS/USD)
- Conversión automática a ARS usando tipo de cambio configurable
- Categorizar transacciones con categorías predefinidas y personalizadas
- Crear metas de ahorro con seguimiento de depósitos y retiros
- Establecer presupuestos mensuales por categoría con alertas visuales
- Visualizar dashboard con resumen financiero y gráficos de distribución
- Comparar gastos e ingresos con el mes anterior

## Capturas de Pantalla

> *Próximamente*

## Stack Tecnológico

| Componente| Tecnología|
|------------|--------------------------------|
| **Backend**| Python 3.11+ / Django 5.x|
| **Frontend**| Django Templates + Bootstrap 5|
| **Base de datos**| SQLite (desarrollo) / PostgreSQL|
| **Gráficos**| Chart.js|
| **Iconos**| Bootstrap Icons|

## Características Principales# Control de Gastos

Aplicación web para el control y seguimiento de finanzas personales desarrollada con Django.

## Descripción

Control de Gastos permite a los usuarios:

- Registrar gastos e ingresos con soporte multimoneda (ARS/USD)
- Conversión automática a ARS usando tipo de cambio configurable
- Categorizar transacciones con categorías predefinidas y personalizadas
- Crear metas de ahorro con seguimiento de depósitos y retiros
- Establecer presupuestos mensuales por categoría con alertas visuales
- Visualizar dashboard con resumen financiero y gráficos de distribución
- Comparar gastos e ingresos con el mes anterior

## Capturas de Pantalla

> *Próximamente*

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| **Backend** | Python 3.11+ / Django 5.x |
| **Frontend** | Django Templates + Bootstrap 5 |
| **Base de datos** | SQLite (desarrollo) / PostgreSQL (producción) |
| **Gráficos** | Chart.js |
| **Iconos** | Bootstrap Icons |

## Características Principales

### 💰 Gestión de Gastos e Ingresos
- Registro con fecha, descripción, monto y categoría
- Soporte multimoneda (ARS/USD) con conversión automática
- Filtros por mes, año y categoría
- Paginación en listados

### 📊 Dashboard Interactivo
- Resumen de balance mensual (ingresos vs gastos)
- Comparación porcentual con mes anterior
- Estado de presupuestos con alertas visuales
- Progreso de metas de ahorro
- Gráfico de distribución de gastos por categoría
- Últimas transacciones

### 🎯 Presupuestos
- Presupuestos mensuales por categoría de gasto
- Umbral de alerta configurable (default 80%)
- Estados: OK, Alerta, Excedido
- Función de copiar presupuestos del mes anterior
- Comparación año contra año

### 🐷 Metas de Ahorro
- Crear metas con objetivo y fecha límite
- Registrar depósitos y retiros
- Seguimiento de progreso porcentual
- Auto-completado cuando se alcanza el objetivo
- Iconos y colores personalizables

### 🏷️ Categorías
- Categorías de sistema predefinidas
- Categorías personalizadas por usuario
- Tipos: Gasto e Ingreso
- Iconos y colores personalizables

## Requisitos Previos

- Python 3.11 o superior
- pip
- Git

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/control_gastos.git
cd control_gastos
```

### 2. Crear y activar entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements/dev.txt
```

### 4. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu-clave-secreta-aqui
DJANGO_SETTINGS_MODULE=config.settings.dev
```

### 5. Aplicar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

Acceder a http://127.0.0.1:8000

## Estructura del Proyecto

```
control_gastos/
├── apps/                   # Aplicaciones Django
│   ├── budgets/           # Presupuestos mensuales
│   ├── categories/        # Gestión de categorías
│   ├── core/              # Mixins, constantes, utilidades
│   ├── expenses/          # Registro de gastos
│   ├── income/            # Registro de ingresos
│   ├── reports/           # Dashboard y reportes
│   ├── savings/           # Metas de ahorro
│   └── users/             # Autenticación y perfiles
├── config/                # Configuración del proyecto
│   └── settings/          # Settings por entorno
├── static/                # Archivos estáticos (CSS, JS)
├── templates/             # Templates HTML
│   ├── components/        # Componentes reutilizables
│   ├── budgets/
│   ├── categories/
│   ├── expenses/
│   ├── income/
│   ├── reports/
│   ├── savings/
│   └── users/
├── requirements/          # Dependencias por entorno
└── manage.py
```

## Apps y Funcionalidades

| App | Descripción | Estado |
|-----|-------------|--------|
| `core` | Mixins (Timestamp, SoftDelete), constantes, utilidades | ✅ |
| `users` | Registro, login, logout, perfil de usuario | ✅ |
| `categories` | CRUD categorías (sistema + personalizadas) | ✅ |
| `expenses` | CRUD gastos, multimoneda, conversión ARS | ✅ |
| `income` | CRUD ingresos, multimoneda, conversión ARS | ✅ |
| `savings` | Metas de ahorro, depósitos/retiros, progreso | ✅ |
| `budgets` | Presupuestos mensuales, alertas, copiar mes anterior | ✅ |
| `reports` | Dashboard con gráficos y resumen financiero | ✅ |

## Modelos Principales

### Expense / Income
- `user` - Usuario propietario
- `category` - Categoría (FK)
- `description` - Descripción
- `amount` - Monto original
- `currency` - Moneda (ARS/USD)
- `exchange_rate` - Tipo de cambio
- `amount_ars` - Monto en ARS (calculado)
- `date` - Fecha
- Hereda: `TimestampMixin`, `SoftDeleteMixin`

### Budget
- `user` - Usuario propietario
- `category` - Categoría de gasto (FK)
- `month` / `year` - Período
- `amount` - Monto presupuestado
- `alert_threshold` - Umbral de alerta (%)
- Propiedades calculadas: `spent_amount`, `spent_percentage`, `status`

### Saving
- `user` - Usuario propietario
- `name` - Nombre de la meta
- `target_amount` - Monto objetivo
- `current_amount` - Monto actual
- `target_date` - Fecha objetivo
- `status` - ACTIVE / COMPLETED / CANCELLED
- Métodos: `add_deposit()`, `add_withdrawal()`

### SavingMovement
- `saving` - Meta de ahorro (FK)
- `type` - DEPOSIT / WITHDRAWAL
- `amount` - Monto del movimiento
- `date` - Fecha

## Configuración por Entorno

| Archivo | Uso |
|---------|-----|
| `config/settings/base.py` | Configuración común |
| `config/settings/dev.py` | Desarrollo (DEBUG=True, SQLite) |
| `config/settings/prod.py` | Producción (DEBUG=False, PostgreSQL) |

## Comandos Útiles

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ejecutar servidor
python manage.py runserver

# Crear superusuario
python manage.py createsuperuser

# Verificar proyecto
python manage.py check

# Shell de Django
python manage.py shell
```

## Flujo de Git

| Rama | Propósito |
|------|-----------|
| `main` | Código estable, listo para producción |
| `develop` | Integración de features |
| `feature/*` | Desarrollo de nuevas funcionalidades |
| `fix/*` | Corrección de bugs |

### Formato de commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(expenses): add expense creation form
fix(budgets): correct alert threshold calculation
perf(reports): optimize dashboard queries
docs(readme): update installation instructions
```

## Roadmap

### MVP ✅ Completado

- [x] Scaffolding del proyecto
- [x] Core: Mixins y utilidades
- [x] Sistema de autenticación
- [x] CRUD de categorías
- [x] CRUD de gastos (multimoneda)
- [x] CRUD de ingresos (multimoneda)
- [x] Metas de ahorro con movimientos
- [x] Presupuestos mensuales con alertas
- [x] Dashboard con gráficos

### Próximas Features

- [ ] Exportación a Excel/PDF
- [ ] Filtros avanzados por rango de fechas
- [ ] Gráficos de evolución mensual
- [ ] Transacciones recurrentes
- [ ] PWA (Progressive Web App)
- [ ] Notificaciones por email
- [ ] Cuentas compartidas (familiar)

## Testing

```bash
# Ejecutar todos los tests
python manage.py test

# Tests de una app específica
python manage.py test apps.expenses

# Con coverage
coverage run manage.py test
coverage report
```

## Licencia

Este proyecto es de uso privado.

## Autor

**Nicolás Kachuk**
