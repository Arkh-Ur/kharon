# Kharōn

> Plataforma de Orquestación y Monitoreo de Scripts

**Arkh-Ur — Data Engineering Division**

[![Version](https://img.shields.io/badge/version-0.4.0--pre-orange)](https://github.com/Arkh-Ur/kharon/releases)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![Airflow](https://img.shields.io/badge/airflow-3.x-green)](https://airflow.apache.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red)]()

Kharōn orquesta scripts existentes **sin modificarlos**, exponiendo monitoreo en tiempo real, ejecución bajo demanda y gestión por cliente a través de una webapp Streamlit.

---

## Stack

| Capa | Tecnología |
|---|---|
| Orquestador | Apache Airflow 3.x |
| Webapp | Streamlit 1.56+ |
| Lenguaje | Python 3.11+ |
| Base de datos | SQLite (dev) / PostgreSQL (prod) |
| Gestor de paquetes | [uv](https://docs.astral.sh/uv/) |

---

## Instalación en Linux / macOS

### Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

```bash
# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Inicio rápido

```bash
git clone https://github.com/Arkh-Ur/kharon.git
cd kharon
chmod +x start_kharon.sh
./start_kharon.sh
```

El script instala dependencias, inicializa Airflow y arranca todos los servicios. La primera ejecución tarda ~60s mientras Airflow procesa los DAGs.

| Servicio | URL |
|---|---|
| Kharōn Webapp | http://localhost:8501 |
| Airflow UI / API | http://localhost:8080 |

La contraseña de Airflow se genera automáticamente en `airflow_home/simple_auth_manager_passwords.json.generated`.

---

## Instalación en Windows

Airflow no tiene soporte oficial nativo en Windows. Hay dos métodos recomendados.

---

### Método 1: Podman (recomendado)

Airflow corre dentro de un contenedor Linux. La webapp Kharōn corre directamente en Windows.

#### Requisitos

- [Podman Desktop](https://podman-desktop.io/) (instala Podman + podman-compose)
- Python 3.11+ para Windows
- [uv](https://docs.astral.sh/uv/): `winget install astral-sh.uv`

#### 1. Clonar el repositorio

```powershell
git clone https://github.com/Arkh-Ur/kharon.git
cd kharon
```

#### 2. Construir la imagen de Airflow

```powershell
podman build -t kharon-airflow -f Containerfile .
```

#### 3. Iniciar el contenedor de Airflow

```powershell
podman run -d `
  --name kharon-airflow `
  -p 8080:8080 `
  -v ${PWD}/airflow_home:/opt/airflow:Z `
  -e AIRFLOW_HOME=/opt/airflow `
  -e AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags `
  -e AIRFLOW__CORE__LOAD_EXAMPLES=false `
  -e AIRFLOW__CORE__EXECUTOR=LocalExecutor `
  -e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////opt/airflow/airflow.db `
  kharon-airflow
```

Verificar que Airflow esté listo:

```powershell
# Esperar ~30s, luego:
Invoke-RestMethod http://localhost:8080/api/v2/monitor/health
```

Obtener la contraseña generada:

```powershell
Get-Content airflow_home\simple_auth_manager_passwords.json.generated | ConvertFrom-Json
```

#### 4. Iniciar la webapp Kharōn

```powershell
# Instalar dependencias
uv sync

# Activar entorno virtual
.venv\Scripts\Activate.ps1

# Configurar conexión a Airflow
$env:KHARON_AIRFLOW_HOST = "localhost"
$env:KHARON_AIRFLOW_PORT = "8080"
$env:KHARON_AIRFLOW_USER = "admin"
$env:KHARON_AIRFLOW_PASSWORD = "<contraseña del paso anterior>"

# Iniciar webapp
cd webapp
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

#### Scripts externos en contenedor

Los scripts en `airflow_home/scripts_externos/` son accesibles por el contenedor gracias al montaje de volumen. Los scripts `.sh` y `.py` corren dentro del contenedor Linux sin ninguna configuración adicional.

#### Detener

```powershell
podman stop kharon-airflow
podman rm kharon-airflow
```

---

### Método 2: WSL2

Corre todo el stack de Kharōn dentro de Windows Subsystem for Linux. La experiencia es idéntica a Linux nativa.

#### Requisitos

- Windows 10/11 con WSL2 activado
- Ubuntu 22.04 o superior desde Microsoft Store

#### 1. Instalar WSL2

```powershell
# En PowerShell como Administrador:
wsl --install -d Ubuntu-24.04
```

Reiniciar Windows cuando se indique.

#### 2. Instalar dependencias en Ubuntu

```bash
# Dentro de la terminal WSL2:
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip git curl
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

#### 3. Clonar y arrancar

```bash
# Clonar en el sistema de archivos de Linux (mejor performance)
cd ~
git clone https://github.com/Arkh-Ur/kharon.git
cd kharon
chmod +x start_kharon.sh
./start_kharon.sh
```

Acceder desde Windows:

| Servicio | URL |
|---|---|
| Kharōn Webapp | http://localhost:8501 |
| Airflow UI | http://localhost:8080 |

> **Nota:** Clonar dentro de `~/` (sistema de archivos Linux) y no en `/mnt/c/` para evitar problemas de performance con SQLite.

---

## Variables de Entorno

Todas las variables tienen valores por defecto funcionales. Solo configurar si se necesita cambiar algo.

| Variable | Default | Descripción |
|---|---|---|
| `KHARON_HOME` | directorio del script | Raíz del proyecto |
| `AIRFLOW_HOME` | `$KHARON_HOME/airflow_home` | Home de Airflow |
| `KHARON_AIRFLOW_HOST` | `localhost` | Host de la API de Airflow |
| `KHARON_AIRFLOW_PORT` | `8080` | Puerto de la API de Airflow |
| `KHARON_AIRFLOW_USER` | `admin` | Usuario de Airflow |
| `KHARON_AIRFLOW_PASSWORD` | auto (del archivo .generated) | Contraseña de Airflow |
| `KHARON_PORT` | `8501` | Puerto de la webapp |

---

## Modos de Ejecución de Scripts

| Modo | Descripción | Schedule Airflow |
|---|---|---|
| **Bajo Demanda** | Solo manual desde la web | `None` |
| **Continuo** | Se re-ejecuta al terminar | `@continuous` |
| **Agendado** | Expresión cron | `0 6 * * *` |

---

## Inicio Manual (sin script)

```bash
source .venv/bin/activate
export AIRFLOW_HOME=$(pwd)/airflow_home

# Cada proceso en una terminal separada:
airflow dag-processor
airflow scheduler
airflow api-server --port 8080

# Webapp:
cd webapp && streamlit run app.py --server.port 8501
```

---

## Tests E2E

Requiere servicios corriendo en los puertos 8501 y 8080.

```bash
uv run pytest tests/e2e/ -v
```

---

## Estructura del Proyecto

```
kharon/
├── airflow_home/
│   ├── dags/
│   │   ├── operators/        # KharonOperator
│   │   ├── utils/            # ScriptRunner, ScriptMonitor
│   │   └── config/           # Registros YAML + logos de clientes
│   └── scripts_externos/     # Scripts externos (nunca se modifican)
├── webapp/
│   ├── app.py                # Entry point (7 páginas)
│   ├── components/           # Componentes UI
│   └── static/               # Logos SVG
├── tests/e2e/                # Tests Playwright
├── Containerfile             # Imagen para Podman/Docker
├── start_kharon.sh           # Inicio Linux/macOS
└── start_kharon.ps1          # Inicio Windows (webapp únicamente)
```

---

## Licencia

Propiedad de Arkh-Ur. Todos los derechos reservados.
