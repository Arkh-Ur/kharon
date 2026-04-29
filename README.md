# Kharōn

> Plataforma de Orquestación y Monitoreo de Scripts

**Arkh-Ur — Data Engineering Division**

[![Version](https://img.shields.io/badge/version-0.1.0--pre-orange)](https://github.com/Arkh-Ur/kharon/releases)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![Airflow](https://img.shields.io/badge/airflow-3.x-green)](https://airflow.apache.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red)]()

---

## Qué es Kharōn?

Kharōn es una plataforma que orquesta scripts existentes **sin modificarlos**, proporcionando monitoreo en tiempo real, ejecución bajo demanda via web, y organización por cliente.

> *En la mitología, Caronte (Kharōn) es el barquero que guía las almas a través del río. De la misma forma, Kharōn guía cada script a través de su flujo de ejecución, monitoreo y registro — sin alterar su naturaleza.*

### Características

- 🎛️ **Dashboard en tiempo real** — Metric cards, timeline Gantt, donut de estados, ejecuciones por cliente
- ⚙️ **Gestión de procesos** — Ver estado, ejecutar, ver logs, eliminar DAGs con confirmación
- 📄 **Visor de logs** — Navegación por DAG → ejecución → tarea con logs completos
- 📡 **Monitoreo global** — Filtros por estado, tipo, cliente y fecha con métricas agregadas
- ❤️ **Salud por cliente** — Health bars, tasas de éxito, fallos consecutivos
- ➕ **Nuevo Script** — Wizard de 5 pasos con validación, preview del script, y cron guide
- 🔧 **Configuración** — CRUD de clientes con logos, colores, descripciones

## Stack

| Capa | Tecnología |
|---|---|
| Orquestador | Apache Airflow 3.x |
| Webapp | Streamlit |
| Lenguaje | Python 3.11+ |
| Base de datos | SQLite (dev) / PostgreSQL (prod) |
| Configuración | YAML |
| Testing | Playwright (E2E) |
| Gestor de paquetes | uv |

## Estructura del Proyecto

```
kharon/
├── airflow_home/         # Airflow home directory
│   ├── dags/             # DAG definitions
│   │   ├── utils/        # ScriptRunner, ScriptMonitor
│   │   ├── operators/    # KharonOperator
│   │   ├── config/       # YAML registries + client logos
│   │   └── scripts/      # Support scripts
│   ├── scripts_externos/ # External scripts (never modified)
│   └── logs/             # Execution logs
├── webapp/               # Kharōn Streamlit webapp
│   ├── app.py            # Main entry point (7 pages, CSS, routing)
│   ├── components/       # UI components (script_form, badges, etc.)
│   ├── static/           # SVG logos
│   └── requirements.txt
├── tests/
│   └── e2e/              # Playwright E2E tests
├── docs/                 # PRD, TRD, Implementation Plan
├── DESIGN_AUDIT.md       # 25 prioritized design improvements
├── start_kharon.sh       # Startup script
└── requirements.txt      # Python dependencies
```

## Inicio Rápido

```bash
# 1. Clonar
git clone https://github.com/Arkh-Ur/kharon.git
cd kharon

# 2. Instalar uv (si no lo tenés)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Sincronizar dependencias
uv sync --extra dev

# 4. Iniciar Kharōn
chmod +x start_kharon.sh
./start_kharon.sh
```

## Puertos

| Servicio | Puerto |
|---|---|
| Airflow API/UI | 8080 |
| Kharōn Webapp | 8501 |

## Modos de Ejecución

| Modo | Descripción | Schedule |
|---|---|---|
| Bajo Demanda | Solo ejecución manual desde la web | `None` |
| Continuo | Se re-ejecuta automáticamente al terminar | `@continuous` |
| Agendado | Según expresión cron | `0 6 * * *` |

## Tests

```bash
# E2E (requiere servicios corriendo en 8501 y 8080)
uv run pytest tests/e2e/ -v
```

## Documentación

- [PRD — Product Requirements Document](docs/PRD.md)
- [TRD — Technical Requirements Document](docs/TRD.md)
- [Plan de Implementación](docs/IMPLEMENTATION_PLAN.md)
- [Changelog](CHANGELOG.md)
- [Design Audit](DESIGN_AUDIT.md)

## Licencia

Propiedad de Arkh-Ur. Todos los derechos reservados.
