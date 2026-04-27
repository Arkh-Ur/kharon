import os
from pathlib import Path

_WEBAPP_DIR = Path(__file__).parent
PROJECT_ROOT = _WEBAPP_DIR.parent

AIRFLOW_HOST = os.getenv("KHARON_AIRFLOW_HOST", "localhost")
AIRFLOW_PORT = int(os.getenv("KHARON_AIRFLOW_PORT", "8080"))
AIRFLOW_USER = os.getenv("KHARON_AIRFLOW_USER", "admin")
AIRFLOW_PASSWORD = os.getenv("KHARON_AIRFLOW_PASSWORD", "admin")
AIRFLOW_BASE_URL = f"http://{AIRFLOW_HOST}:{AIRFLOW_PORT}"

KHARON_PORT = int(os.getenv("KHARON_PORT", "8501"))

AIRFLOW_HOME = Path(os.getenv("AIRFLOW_HOME", str(PROJECT_ROOT / "airflow_home")))
DAGS_DIR = AIRFLOW_HOME / "dags"
CONFIG_DIR = DAGS_DIR / "config"
SCRIPTS_REGISTRY_PATH = CONFIG_DIR / "scripts_registry.yaml"
CLIENTS_REGISTRY_PATH = CONFIG_DIR / "clients_registry.yaml"
MONITORING_DIR = AIRFLOW_HOME / "logs" / "kharon_monitoring"
EXTERNAL_SCRIPTS_DIR = AIRFLOW_HOME / "scripts_externos"

APP_NAME = "Kharōn"
COMPANY = "Arkh-Ur"
PRIMARY_COLOR = "#4a1a8a"
SECONDARY_COLOR = "#0d6efd"
SUCCESS_COLOR = "#198754"
WARNING_COLOR = "#fd7e14"
DANGER_COLOR = "#dc3545"


def get_kharon_home() -> Path:
    return PROJECT_ROOT


def ensure_directories():
    for d in [AIRFLOW_HOME, DAGS_DIR, CONFIG_DIR, MONITORING_DIR,
              EXTERNAL_SCRIPTS_DIR, DAGS_DIR / "operators",
              DAGS_DIR / "utils", DAGS_DIR / "scripts"]:
        d.mkdir(parents=True, exist_ok=True)


ensure_directories()
