# Kharōn

> Plataforma de Orquestación y Monitoreo de Scripts

**Arkh-Ur — Data Engineering Division**

---

## Que es Kharōn?

Kharōn es una plataforma que orquesta scripts existentes sin modificarlos, proporcionando monitoreo en tiempo real, ejecucion bajo demanda via web, y organizacion por cliente.

> *En la mitologia, Caronte (Kharōn) es el barquero que guia las almas a traves del rio. De la misma forma, Kharōn guia cada script a traves de su flujo de ejecucion, monitoreo y registro — sin alterar su naturaleza.*

## Stack

| Capa | Tecnologia |
|---|---|
| Orquestador | Apache Airflow 3.x |
| Webapp | Streamlit |
| Lenguaje | Python 3.10+ |
| Base de datos | SQLite (dev) / PostgreSQL (prod) |
| Configuracion | YAML |

## Estructura del Proyecto

```
kharon/
├── airflow_home/         # Airflow home directory
│   ├── dags/             # DAG definitions
│   │   ├── utils/        # Shared utilities
│   │   ├── operators/    # Custom operators
│   │   ├── config/       # YAML registries
│   │   └── scripts/      # Support scripts
│   ├── scripts_externos/ # External scripts (not modified)
│   └── logs/             # Execution logs
├── webapp/               # Kharōn Streamlit webapp
│   ├── app.py            # Main entry point
│   ├── components/       # UI components
│   └── requirements.txt
├── docs/                 # PRD, TRD, Implementation Plan
├── start_kharon.sh       # Startup script
└── requirements.txt      # Python dependencies
```

## Inicio Rapido

```bash
# 1. Clonar
git clone https://github.com/Arkh-Ur/kharon.git
cd kharon

# 2. Crear virtualenv
python3 -m venv airflow_venv
source airflow_venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar Airflow
export AIRFLOW_HOME=$(pwd)/airflow_home
airflow db migrate

# 5. Iniciar Kharōn
chmod +x start_kharon.sh
./start_kharon.sh
```

## Puertos

| Servicio | Puerto |
|---|---|
| Airflow API/UI | 8080 |
| Kharōn Webapp | 8501 |

## Documentacion

- [PRD — Product Requirements Document](docs/PRD.md)
- [TRD — Technical Requirements Document](docs/TRD.md)
- [Plan de Implementacion](docs/IMPLEMENTATION_PLAN.md)

## Licencia

Propiedad de Arkh-Ur. Todos los derechos reservados.
