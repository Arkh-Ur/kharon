"""
Configuration module for Kharōn webapp.

Manages environment variables, application configuration, and path management.
"""

import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration class for Kharōn application."""
    
    # Airflow configuration
    AIRFLOW_HOST: str = os.getenv("KHARON_AIRFLOW_HOST", "localhost")
    AIRFLOW_PORT: int = int(os.getenv("KHARON_AIRFLOW_PORT", "8080"))
    AIRFLOW_USER: str = os.getenv("KHARON_AIRFLOW_USER", "admin")
    AIRFLOW_PASSWORD: str = os.getenv("KHARON_AIRFLOW_PASSWORD", "admin")
    
    @property
    def AIRFLOW_BASE_URL(self) -> str:
        """Construct Airflow base URL from host and port."""
        return f"http://{self.AIRFLOW_HOST}:{self.AIRFLOW_PORT}"
    
    # Kharōn webapp configuration
    KHARON_PORT: int = int(os.getenv("KHARON_PORT", "8501"))
    
    # Path configuration
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    AIRFLOW_HOME: Path = Path(os.getenv("AIRFLOW_HOME", str(PROJECT_ROOT / "airflow_home")))
    DAGS_DIR: Path = AIRFLOW_HOME / "dags"
    CONFIG_DIR: Path = DAGS_DIR / "config"
    SCRIPTS_REGISTRY_PATH: Path = CONFIG_DIR / "scripts_registry.yaml"
    CLIENTS_REGISTRY_PATH: Path = CONFIG_DIR / "clients_registry.yaml"
    MONITORING_DIR: Path = AIRFLOW_HOME / "data" / "monitoring"
    EXTERNAL_SCRIPTS_DIR: Path = PROJECT_ROOT / "airflow_home" / "scripts_externos"
    
    # Branding
    APP_NAME: str = "Kharōn"
    COMPANY: str = "Arkh-Ur"
    PRIMARY_COLOR: str = "#4a1a8a"
    
    def get_kharon_home(self) -> Path:
        """Get the Kharōn home directory path."""
        return Path(__file__).parent.parent
    
    def validate_directories(self) -> None:
        """Validate that required directories exist."""
        required_dirs = [
            self.AIRFLOW_HOME,
            self.DAGS_DIR,
            self.CONFIG_DIR,
            self.MONITORING_DIR,
            self.EXTERNAL_SCRIPTS_DIR,
            self.CONFIG_DIR.parent,  # Ensure utils directory exists
            self.DAGS_DIR / "operators",
            self.DAGS_DIR / "scripts",
            self.DAGS_DIR / "utils",
        ]
        
        for directory in required_dirs:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment configuration information."""
        return {
            "app_name": self.APP_NAME,
            "company": self.COMPANY,
            "primary_color": self.PRIMARY_COLOR,
            "airflow_base_url": self.AIRFLOW_BASE_URL,
            "airflow_host": self.AIRFLOW_HOST,
            "airflow_port": self.AIRFLOW_PORT,
            "airflow_user": self.AIRFLOW_USER,
            "kharon_port": self.KHARON_PORT,
            "project_root": str(self.PROJECT_ROOT),
            "airflow_home": str(self.AIRFLOW_HOME),
            "dags_dir": str(self.DAGS_DIR),
            "config_dir": str(self.CONFIG_DIR),
            "monitoring_dir": str(self.MONITORING_DIR),
            "external_scripts_dir": str(self.EXTERNAL_SCRIPTS_DIR),
        }


# Global configuration instance
config = Config()

# Ensure required directories exist on import
config.validate_directories()