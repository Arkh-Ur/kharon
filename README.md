# Kharōn

> Plataforma de Orquestación y Monitoreo de Scripts

**Arkh-Ur — Data Engineering Division**

[![Version](https://img.shields.io/badge/version-0.7.0-blue)](https://github.com/Arkh-Ur/kharon/releases)
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

## Instalación con Contenedor (Windows / Linux / macOS)

> La forma más simple de correr Kharōn. **No requiere instalar Python ni clonar el repositorio.**
> La imagen se publica automáticamente en `ghcr.io/arkh-ur/kharon` via GitHub Actions.

---

### Paso 1 — Instalar Podman

Descargá e instalá **[Podman Desktop](https://podman-desktop.io/)** (incluye todo lo necesario).

> También funciona con Docker — reemplazá `podman` por `docker` en los comandos y quitá `:Z` de los volúmenes.

---

### Paso 2 — Crear la carpeta de datos

Esta carpeta guarda toda la información de Kharōn (DAGs, clientes, scripts) entre reinicios.

**Linux / macOS** — en una terminal:
```bash
mkdir -p ~/kharon-data/airflow_home
```

**Windows** — en PowerShell:
```powershell
New-Item -ItemType Directory -Force -Path C:\kharon-data\airflow_home
```

---

### Paso 3 — Iniciar Kharōn

**Linux / macOS:**
```bash
podman run -d --name kharon \
  -p 8080:8080 \
  -p 8501:8501 \
  -v ~/kharon-data/airflow_home:/opt/airflow:Z \
  ghcr.io/arkh-ur/kharon:latest
```

**Windows (PowerShell):**
```powershell
podman run -d --name kharon `
  -p 8080:8080 `
  -p 8501:8501 `
  -v C:\kharon-data\airflow_home:/opt/airflow `
  ghcr.io/arkh-ur/kharon:latest
```

> **Primera ejecución:** Podman descarga la imagen (~800 MB) y arranca Airflow. Esperá **1-2 minutos** antes de abrir el navegador.
>
> **Ejecuciones siguientes:** arranca en ~5 segundos.

---

### Paso 4 — Abrir la webapp

Una vez iniciado, abrí estas URLs en el navegador:

| Servicio | URL |
|---|---|
| **Kharōn Webapp** | **http://localhost:8501** |
| Airflow UI | http://localhost:8080 |

---

### Paso 5 — Obtener la contraseña de Airflow

La contraseña se genera automáticamente la primera vez. Para verla:

```bash
podman exec kharon cat /opt/airflow/simple_auth_manager_passwords.json.generated
```

Verás algo como: `{"admin": "xK9mPqR2"}` — el valor entre comillas es la contraseña.
El usuario siempre es `admin`.

---

### Detener y reiniciar

```bash
# Detener
podman stop kharon

# Reiniciar (los datos persisten)
podman start kharon

# Ver logs si algo no arranca
podman logs kharon --tail 30
```

---

### Actualizar a una nueva versión

```bash
podman stop kharon && podman rm kharon
podman pull ghcr.io/arkh-ur/kharon:latest
```

Luego repetí el comando del **Paso 3**.

---

<details>
<summary><strong>Opciones avanzadas</strong></summary>

#### Exponer scripts del host al contenedor

Para gestionar scripts que ya tenés en tu máquina, agregá un volumen adicional:

```bash
# Linux / macOS
podman run -d --name kharon \
  -p 8080:8080 -p 8501:8501 \
  -v ~/kharon-data/airflow_home:/opt/airflow:Z \
  -v /ruta/a/tus/scripts:/scripts:Z \
  ghcr.io/arkh-ur/kharon:latest
```

Al registrar un nuevo script desde la webapp usá la ruta `/scripts/...`.

#### Tags de imagen disponibles

| Tag | Se publica | Uso recomendado |
|---|---|---|
| `latest` | Cada push a `main` | Staging / siempre actualizado |
| `0.7.0` | Al crear el tag `v0.7.0` | **Producción** (versión fija) |
| `sha-a1b2c3` | Cada commit | Traceability / rollback |

```bash
# Usar versión fija para producción
podman run ... ghcr.io/arkh-ur/kharon:0.6.1

# Ver qué versión está corriendo
podman exec kharon git -C /opt/kharon describe --tags --always
```

#### Auto-update al iniciar

Con `AUTO_UPDATE=true` el contenedor hace `git pull` antes de arrancar (útil en staging):

```bash
podman run -d --name kharon \
  -e AUTO_UPDATE=true \
  -p 8080:8080 -p 8501:8501 \
  -v ~/kharon-data/airflow_home:/opt/airflow:Z \
  ghcr.io/arkh-ur/kharon:latest
```

#### Script launcher (si ya clonaste el repo)

```bash
git clone https://github.com/Arkh-Ur/kharon.git && cd kharon
chmod +x podman-run.sh && ./podman-run.sh   # Linux/macOS
.\start_kharon.ps1 -Podman                  # Windows PowerShell
```

#### Construir la imagen localmente

```bash
git clone https://github.com/Arkh-Ur/kharon.git && cd kharon
podman build -t ghcr.io/arkh-ur/kharon:latest .

# Con tag específico
podman build --build-arg KHARON_BRANCH=v0.6.1 -t kharon:v0.6.1 .
```

</details>

---

## Instalación en Windows (nativa sin contenedor)

Airflow no tiene soporte oficial nativo en Windows. Si no querés usar contenedor, la alternativa es WSL2.

---

### WSL2

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

### Alternativa: WSL 1 + PostgreSQL (Troubleshooting / Máquinas Virtuales)

Si estás ejecutando Windows **dentro de una Máquina Virtual (ej. QEMU, VirtualBox, AWS)** sin soporte para *Nested Virtualization* (Virtualización Anidada), herramientas como Podman o WSL2 fallarán con el error `HCS_E_HYPERV_NOT_INSTALLED`. 

La solución es utilizar **WSL versión 1**, que no requiere hipervisor de hardware, combinada con **PostgreSQL**, ya que WSL1 tiene un bug conocido con el protocolo de bloqueo de archivos (`locking protocol`) que usa SQLite por defecto en Airflow.

#### 1. Forzar WSL a versión 1 e instalar Ubuntu
```powershell
# En PowerShell:
wsl --set-default-version 1
wsl --install -d Ubuntu
```

#### 2. Instalar PostgreSQL en WSL1
WSL1 requiere iniciar el servicio manualmente porque no soporta `systemd`.

```bash
# Dentro de la terminal WSL:
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo service postgresql start

# Configurar usuario y base de datos para Airflow
sudo -u postgres psql -c "CREATE USER airflow WITH PASSWORD 'airflow';"
sudo -u postgres psql -c "CREATE DATABASE airflow;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;"
sudo -u postgres psql -c "ALTER DATABASE airflow OWNER TO airflow;"
```

#### 3. Instalar Airflow y conectarlo a PostgreSQL
```bash
# Instalar uv y crear entorno
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

uv venv ~/airflow-env
source ~/airflow-env/bin/activate

# Instalar Airflow + Drivers de Postgres (psycopg2 y asyncpg)
uv pip install "apache-airflow==3.2.0" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.2.0/constraints-3.12.txt" --link-mode=copy
uv pip install psycopg2-binary asyncpg
```

#### 4. Ejecutar
```bash
# Configurar la conexión a PostgreSQL en lugar de SQLite
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN='postgresql+psycopg2://airflow:airflow@localhost/airflow'
export AIRFLOW__CORE__EXECUTOR='LocalExecutor'

# Ejecutar el servidor (creará las tablas en Postgres automáticamente)
airflow standalone
```

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

Kharōn soporta dos modos de base de datos para Airflow:

| Modo | Cuándo | Persistencia |
|------|--------|-------------|
| **SQLite** | Default (nativo Linux/macOS) | `airflow_home/airflow.db` |
| **PostgreSQL embedded** | Podman (automático) | `airflow_home/postgres/` volumen |

#### Podman — PostgreSQL incluido

El contenedor incluye PostgreSQL. Se inicializa automáticamente en el primer run y los datos persisten en el volumen `airflow_home/postgres/`. No hay que configurar nada.

#### Nativo (Linux/macOS) — PostgreSQL externo

```bash
# Exportar variables antes de ejecutar start_kharon.sh:
export POSTGRES_HOST=localhost
export POSTGRES_USER=airflow
export POSTGRES_PASSWORD=secret
export POSTGRES_DB=kharon
./start_kharon.sh

# O con connection string completo:
export DATABASE_URL="postgresql+psycopg2://airflow:secret@localhost:5432/kharon"
./start_kharon.sh
```

#### Nativo (Windows) — PostgreSQL externo

```powershell
.\start_kharon.ps1 -PostgresHost localhost -PostgresPassword secret
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
├── start_kharon.ps1          # Inicio Windows (nativo + Podman)
├── start_daemon.ps1          # Inicio Windows modo Demonio (Segundo plano)
├── stop_daemon.ps1           # Detener Demonio
└── install_service.ps1       # Instalar como servicio de arranque automático
```

---

## Licencia

Propiedad de Arkh-Ur. Todos los derechos reservados.
