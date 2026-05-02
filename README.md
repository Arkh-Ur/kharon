# Kharōn

> Plataforma de Orquestación y Monitoreo de Scripts

**Arkh-Ur — Data Engineering Division**

[![Version](https://img.shields.io/badge/version-0.5.1-blue)](https://github.com/Arkh-Ur/kharon/releases)
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

### Método 1: Podman — All-in-One (recomendado)

Airflow y la webapp Kharōn corren juntos en un único contenedor. El código se clona automáticamente desde GitHub durante el build.

#### Requisitos

- [Podman](https://podman.io/) o [Podman Desktop](https://podman-desktop.io/)

#### Inicio rápido

```powershell
git clone https://github.com/Arkh-Ur/kharon.git
cd kharon

# Construir la imagen (clona el repo de GitHub)
podman build -t kharon:latest .

# Iniciar
.\podman-run.sh       # Linux/macOS
.\start_kharon.ps1 -Podman   # Windows
```

| Servicio | URL |
|---|---|
| Kharōn Webapp | http://localhost:8501 |
| Airflow UI / API | http://localhost:8080 |

#### Mantener actualizado

```bash
# Reconstruir con el último código del repo:
podman rmi kharon:latest && ./podman-run.sh

# O actualizar automáticamente al iniciar (sin rebuild):
AUTO_UPDATE=true ./podman-run.sh        # Linux/macOS
.\start_kharon.ps1 -Podman -AutoUpdate  # Windows
```

#### Build con tag específico

```bash
podman build --build-arg KHARON_BRANCH=v0.5.1 -t kharon:v0.5.1 .
```

#### Datos persistentes

Solo `airflow_home/` se monta como volumen — DAGs generados, registros de clientes y scripts externos persisten entre reinicios.

#### Verificación

```bash
curl http://localhost:8080/api/v2/monitor/health
curl http://localhost:8501/_stcore/health

# Ver versión corriendo
podman exec kharon git -C /opt/kharon describe --tags --always
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

### General

| Variable | Default | Descripción |
|---|---|---|
| `KHARON_HOME` | directorio del script | Raíz del proyecto |
| `AIRFLOW_HOME` | `$KHARON_HOME/airflow_home` | Home de Airflow |
| `KHARON_AIRFLOW_HOST` | `localhost` | Host de la API de Airflow |
| `KHARON_AIRFLOW_PORT` | `8080` | Puerto de la API de Airflow |
| `KHARON_AIRFLOW_USER` | `admin` | Usuario de Airflow |
| `KHARON_AIRFLOW_PASSWORD` | auto (del archivo .generated) | Contraseña de Airflow |
| `KHARON_PORT` | `8501` | Puerto de la webapp |
| `AUTO_UPDATE` | `false` | `git pull` al iniciar (Podman) |

### PostgreSQL (opcional — por defecto usa SQLite)

| Variable | Default | Descripción |
|---|---|---|
| `DATABASE_URL` | — | Connection string completo: `postgresql+psycopg2://user:pass@host:5432/db` |
| `POSTGRES_HOST` | — | Host de PostgreSQL (si se setea, usa PostgreSQL en vez de SQLite) |
| `POSTGRES_PORT` | `5432` | Puerto de PostgreSQL |
| `POSTGRES_USER` | `airflow` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | — | Contraseña de PostgreSQL |
| `POSTGRES_DB` | `airflow` | Base de datos de PostgreSQL |

#### Ejemplo con PostgreSQL

```bash
# Linux/macOS (nativo):
export POSTGRES_HOST=db.example.com
export POSTGRES_USER=airflow
export POSTGRES_PASSWORD=secret
export POSTGRES_DB=kharon
./start_kharon.sh

# Podman:
POSTGRES_HOST=db.example.com POSTGRES_PASSWORD=secret ./podman-run.sh

# Windows (Podman):
.\start_kharon.ps1 -PostgresHost db.example.com -PostgresPassword secret

# O con DATABASE_URL completo:
export DATABASE_URL="postgresql+psycopg2://airflow:secret@db.example.com:5432/kharon"
./start_kharon.sh
```

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
├── Containerfile             # All-in-one image (Airflow + Streamlit)
├── docker-entrypoint.sh      # Container entrypoint
├── podman-run.sh             # Podman launcher (Linux/macOS)
├── start_kharon.sh           # Inicio Linux/macOS (nativo)
└── start_kharon.ps1          # Inicio Windows (nativo + Podman)
```

---

## Licencia

Propiedad de Arkh-Ur. Todos los derechos reservados.
