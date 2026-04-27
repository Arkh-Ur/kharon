"""
Shared constants for the Kharōn platform.

Defines all project paths, configuration values, and color schemes.
"""

import pathlib
from typing import Dict

CURRENT_FILE = pathlib.Path(__file__).resolve()
KHARON_HOME = CURRENT_FILE.parents[3]
AIRFLOW_HOME = KHARON_HOME / "airflow_home"
DAGS_DIR = AIRFLOW_HOME / "dags"
CONFIG_DIR = DAGS_DIR / "config"
SCRIPTS_DIR = DAGS_DIR / "scripts"
EXTERNAL_SCRIPTS_DIR = AIRFLOW_HOME / "scripts_externos"
LOGS_DIR = AIRFLOW_HOME / "logs"
MONITORING_DIR = LOGS_DIR / "kharon_monitoring"
DATA_DIR = AIRFLOW_HOME / "data"

SCRIPTS_REGISTRY_PATH = CONFIG_DIR / "scripts_registry.yaml"
CLIENTS_REGISTRY_PATH = CONFIG_DIR / "clients_registry.yaml"
MONITORING_RULES_PATH = CONFIG_DIR / "monitoring_rules.yaml"

DAG_PREFIX = "kharon_"

DEFAULT_TIMEOUT_SECONDS = 3600
DEFAULT_RETRIES = 2
MAX_HISTORY_ENTRIES = 100

HEALTHY_SUCCESS_RATE = 0.8
HEALTHY_MAX_CONSECUTIVE_FAILURES = 3
ARKH_UR_COLORS: Dict[str, str] = {
    "primary": "#4a1a8a",
    "secondary": "#0d6efd", 
    "success": "#198754",
    "warning": "#fd7e14",
    "danger": "#dc3545",
    "purple": "#6f42c1"
}

def ensure_directories():
    directories = [
        CONFIG_DIR,
        SCRIPTS_DIR,
        EXTERNAL_SCRIPTS_DIR,
        LOGS_DIR,
        MONITORING_DIR,
        DATA_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
ensure_directories()