import os
import yaml
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
KHARON_CONFIG_PATH = AIRFLOW_HOME / "config" / "kharon_config.yaml"

CONFIG_DIR = AIRFLOW_HOME / "dags" / "config"
SCRIPTS_REGISTRY_PATH = CONFIG_DIR / "scripts_registry.yaml"
GENERATED_SCRIPTS_PATH = CONFIG_DIR / "generated_scripts.yaml"
CLIENTS_REGISTRY_PATH = CONFIG_DIR / "clients_registry.yaml"
MONITORING_DIR = AIRFLOW_HOME / "logs" / "kharon_monitoring"
EXTERNAL_SCRIPTS_DIR = AIRFLOW_HOME / "scripts_externos"


def load_kharon_config() -> dict:
    if KHARON_CONFIG_PATH.is_file():
        try:
            with open(KHARON_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def save_kharon_config(updates: dict) -> None:
    current = load_kharon_config()
    current.update(updates)
    KHARON_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    from utils import atomic_write
    atomic_write(str(KHARON_CONFIG_PATH), yaml.dump(current, allow_unicode=True, default_flow_style=False))


def get_dags_dir() -> Path:
    env_val = os.getenv("KHARON_AIRFLOW_DAGS_DIR")
    if env_val:
        return Path(env_val)
    cfg = load_kharon_config()
    cfg_val = cfg.get("airflow_dags_dir")
    if cfg_val:
        return Path(cfg_val)
    return AIRFLOW_HOME / "dags"


def get_airflow_url() -> str:
    host = os.getenv("KHARON_AIRFLOW_HOST", "localhost")
    port = os.getenv("KHARON_AIRFLOW_PORT", "8080")
    return f"http://{host}:{port}"


DAGS_DIR = get_dags_dir()

APP_NAME = "Kharōn"
COMPANY = "Arkh-Ur"
PRIMARY_COLOR = "#374151"
SECONDARY_COLOR = "#1E2632"
SUCCESS_COLOR = "#22c55e"
WARNING_COLOR = "#f59e0b"
DANGER_COLOR = "#ef4444"
BG_DARK = "#0A0F18"
BG_DARKER = "#131923"
BG_MEDIUM = "#1E2632"
BORDER_COLOR = "#545B67"


def get_kharon_home() -> Path:
    return PROJECT_ROOT


def ensure_directories():
    for d in [AIRFLOW_HOME, get_dags_dir(), CONFIG_DIR, MONITORING_DIR,
              EXTERNAL_SCRIPTS_DIR, get_dags_dir() / "operators",
              get_dags_dir() / "utils", get_dags_dir() / "scripts"]:
        d.mkdir(parents=True, exist_ok=True)


ensure_directories()
