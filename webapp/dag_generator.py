"""
DAG file generator for Kharōn webapp.

Generates Airflow DAG files from script metadata and manages script registry.
"""

import os
import re
import threading
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import config
from utils import atomic_write


@dataclass
class DAGGenerationResult:
    """Result of DAG generation operation."""
    success: bool
    dag_id: Optional[str] = None
    file_path: Optional[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        """Initialize empty list for errors."""
        if self.errors is None:
            self.errors = []


class DAGGenerator:
    """DAG file generator with validation and registry management."""
    
    def __init__(self, dags_dir: Optional[Path] = None, registry_path: Optional[Path] = None):
        """Initialize DAGGenerator.
        
        Args:
            dags_dir: Directory for DAG files. If None, uses config.DAGS_DIR
            registry_path: Path for scripts registry. If None, uses config.SCRIPTS_REGISTRY_PATH
        """
        self.dags_dir = dags_dir or config.get_dags_dir()
        self.registry_path = registry_path or config.GENERATED_SCRIPTS_PATH
        self._lock = threading.RLock()

        # Ensure directories exist
        self.dags_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
    
    def generate_dag(
        self,
        script_id: str,
        script_name: str,
        script_path: str,
        client_id: str,
        timeout: int = 3600,
        retries: int = 2,
        schedule: Optional[str] = None,
        criticality: str = "medium",
        tags: Optional[List[str]] = None,
        python: str = "python3",
        execution_mode: str = "scheduled",
        config_file: Optional[str] = None,
        project_path: Optional[str] = None
    ) -> DAGGenerationResult:
        """Generate a DAG file from script metadata.
        
        Args:
            script_id: Unique script identifier
            script_name: Human-readable script name
            script_path: Path to the script file
            client_id: Associated client identifier
            timeout: Task timeout in seconds
            retries: Number of retry attempts
            schedule: Optional schedule string
            criticality: Criticality level (low, medium, high)
            tags: Optional list of tags
            python: Python executable path
            execution_mode: Execution mode (on_demand, continuous, scheduled)
            
        Returns:
            DAGGenerationResult with operation status
            
        Raises:
            ValueError: If validation fails
            IOError: If file operations fail
        """
        result = DAGGenerationResult(success=False)
        
        try:
            with self._lock:
                # Sanitize script ID first
                sanitized_script_id = self._sanitize_script_id(script_id)

                # Validate sanitized script ID (catches reserved words after normalization)
                validation_error = self._validate_script_id(sanitized_script_id)
                if validation_error:
                    result.errors.append(f"Script ID validation failed: {validation_error}")
                    return result
                
                # Validate script exists
                script_file = Path(os.path.expanduser(script_path))
                if not script_file.exists():
                    result.errors.append(f"Script file not found: {script_path}")
                    return result
                
                # Check if script has valid extension
                if script_file.suffix.lower() not in ['.py', '.sh', '.bash', '.ps1', '.exe', '.bat', '.cmd']:
                    result.errors.append(f"Unsupported script extension: {script_file.suffix}")
                    return result
                
                # Generate DAG content
                dag_content = self._generate_dag_content(
                    sanitized_script_id,
                    script_name,
                    script_file,
                    client_id,
                    timeout,
                    retries,
                    schedule,
                    criticality,
                    tags,
                    python,
                    execution_mode,
                    config_file
                )
                
                # Write DAG file
                dag_file_path = self.dags_dir / f"{sanitized_script_id}.py"
                atomic_write(str(dag_file_path), dag_content)
                
                registry_entry = {
                    "script_id": sanitized_script_id,
                    "script_name": script_name,
                    "script_path": str(script_file),
                    "client_id": client_id,
                    "timeout": timeout,
                    "retries": retries,
                    "schedule": schedule,
                    "criticality": criticality,
                    "tags": tags or [],
                    "python": python,
                    "execution_mode": execution_mode,
                    "config_file": config_file,
                    "project_path": project_path,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                self._update_registry(registry_entry)
                
                result.success = True
                result.dag_id = sanitized_script_id
                result.file_path = str(dag_file_path)
                
                return result
            
        except Exception as e:
            result.errors.append(f"Unexpected error: {str(e)}")
            return result
    
    def update_execution_mode(
        self,
        script_id: str,
        execution_mode: str,
        schedule: Optional[str] = None,
    ) -> DAGGenerationResult:
        """Update execution mode for an existing DAG.
        
        Regenerates the DAG file with new schedule and updates registry.
        
        Args:
            script_id: Script identifier
            execution_mode: New execution mode (on_demand, continuous, scheduled)
            schedule: Cron expression (required if mode is 'scheduled')
            
        Returns:
            DAGGenerationResult with operation status
        """
        result = DAGGenerationResult(success=False)

        try:
            with self._lock:
                registry_data = self._load_registry()

                if script_id not in registry_data:
                    result.errors.append(f"Script not found in registry: {script_id}")
                    return result

                entry = registry_data[script_id]
                entry["execution_mode"] = execution_mode
                entry["schedule"] = schedule if execution_mode == "scheduled" else None

                _raw_path = entry.get("script_path")
                if not _raw_path:
                    result.errors.append(f"No script_path found in registry for: {script_id}")
                    return result
                script_file = Path(_raw_path)
                if not script_file.exists():
                    result.errors.append(f"Script file not found: {_raw_path}")
                    return result

                dag_content = self._generate_dag_content(
                    dag_id=script_id,
                    script_name=entry.get("script_name", script_id),
                    script_file=script_file,
                    client_id=entry.get("client_id", ""),
                    timeout=entry.get("timeout", 3600),
                    retries=entry.get("retries", 2),
                    schedule=entry["schedule"],
                    criticality=entry.get("criticality", "media"),
                    tags=entry.get("tags", []),
                    python=entry.get("python", "python3"),
                    execution_mode=execution_mode,
                    config_file=entry.get("config_file"),
                )

                dag_file_path = self.dags_dir / f"{script_id}.py"
                atomic_write(str(dag_file_path), dag_content)

                registry_data[script_id] = entry
                self._save_registry(registry_data)

            result.success = True
            result.dag_id = script_id
            result.file_path = str(dag_file_path)

            return result
            
        except Exception as e:
            result.errors.append(f"Unexpected error: {str(e)}")
            return result
    
    def delete_dag(self, script_id: str) -> bool:
        """Delete a DAG file and remove from registry.
        
        Args:
            script_id: The script identifier
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            ValueError: If script ID validation fails
            IOError: If file operations fail
"""
        try:
            sanitized_script_id = self._sanitize_script_id(script_id)

            validation_error = self._validate_script_id(sanitized_script_id)
            if validation_error:
                raise ValueError(f"Script ID validation failed: {validation_error}")
            
            dag_file = self.dags_dir / f"{sanitized_script_id}.py"
            if dag_file.exists():
                dag_file.unlink()
            
            self._remove_from_registry(sanitized_script_id)
            
            return True
            
        except ValueError:
            raise
        except Exception:
            return False
    
    def _generate_dag_content(
        self,
        dag_id: str,
        script_name: str,
        script_file: Path,
        client_id: str,
        timeout: int,
        retries: int,
        schedule: Optional[str],
        criticality: str,
        tags: Optional[List[str]],
        python: str,
        execution_mode: str,
        config_file: Optional[str] = None
    ) -> str:
        """Generate complete DAG file content.
        
        Args:
            dag_id: DAG identifier
            script_name: Human-readable script name
            script_file: Path to script file
            client_id: Associated client identifier
            timeout: Task timeout in seconds
            retries: Number of retry attempts
            schedule: Optional schedule string
            criticality: Criticality level
            tags: Optional list of tags
            python: Python executable path
            execution_mode: Execution mode (on_demand, continuous, scheduled)
            
        Returns:
            Complete DAG file content as string
        """
        # Generate schedule based on execution mode
        if execution_mode == "on_demand":
            schedule_param = None
        elif execution_mode == "continuous":
            schedule_param = "@continuous"
        else:
            schedule_param = schedule

        # Build DAG tags
        dag_tags = ["kharon-auto", f"client_{self._sanitize_script_id(client_id)}"]
        if tags:
            dag_tags.extend(tags)

        schedule_str = "None" if schedule_param is None else repr(schedule_param)
        # on_demand y continuous siempre con max_active_runs=1:
        # - on_demand: evita que múltiples triggers ejecuten en paralelo (single run)
        # - continuous: requerido por ContinuousTimetable en Airflow 3.x
        max_active = "\n    max_active_runs=1," if execution_mode in ("on_demand", "continuous") else ""

        if config_file:
            config_arg = f"\n    args=['--config', {repr(str(config_file))}],"
        else:
            config_arg = ""

        # Validate dag_id contains only safe characters for Python identifiers
        if dag_id and not re.match(r'^[a-z][a-z0-9_]*$', dag_id):
            raise ValueError(
                f"Invalid dag_id '{dag_id}': must contain only [a-z0-9_] "
                "and start with a letter after sanitization"
            )

        # Use repr() to properly escape all user-controlled values for Python source embedding
        _safe_script_name = repr(script_name)
        _safe_client_id = repr(client_id)

        # Sanitize values for use inside triple-quoted docstring (prevent docstring injection)
        _safe_doc_name = script_name.replace('\\', '\\\\').replace('"""', "'''")
        _safe_doc_client = client_id.replace('\\', '\\\\').replace('"""', "'''")

        dag_content = f'''"""
Generated DAG for {_safe_doc_name}
Script ID: {dag_id}
Client: {_safe_doc_client}
Execution Mode: {execution_mode}
Generated by Kharōn
"""

from datetime import datetime, timedelta
from airflow import DAG
from operators.kharon_operator import KharonOperator

default_args = {{
    'owner': 'arkh-ur',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': {retries},
    'retry_delay': timedelta(minutes=5),
}}

dag = DAG(
    dag_id='{dag_id}',
    default_args=default_args,
    description={_safe_script_name},
    schedule={schedule_str},{max_active}
    tags={dag_tags!r},
    catchup=False,
    is_paused_upon_creation=False,
)

{dag_id}_task = KharonOperator(
    task_id='execute_{dag_id}',
    script_path={repr(str(script_file))},
    script_id='{dag_id}',
    client_id={_safe_client_id},
    timeout={timeout},{config_arg}
    dag=dag,
)
'''
        
        return dag_content.strip()
    
    def _update_registry(self, entry: Dict) -> None:
        try:
            with self._lock:
                registry_data = self._load_registry()
                registry_data[entry["script_id"]] = entry
                self._save_registry(registry_data)
        except Exception as e:
            raise IOError(f"Failed to update registry: {e}") from e

    def _remove_from_registry(self, script_id: str) -> None:
        try:
            with self._lock:
                registry_data = self._load_registry()
                if script_id in registry_data:
                    del registry_data[script_id]
                
                self._save_registry(registry_data)
                
        except Exception as e:
            raise IOError(f"Failed to remove from registry: {e}") from e
    
    def _load_registry(self) -> Dict:
        """Load scripts registry from file.
        
        Returns:
            Registry data as dict
            
        Raises:
            IOError: If file operations fail
            yaml.YAMLError: If YAML parsing fails
        """
        try:
            if self.registry_path.exists():
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            return {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in registry: {e}") from e
        except IOError as e:
            raise IOError(f"Failed to load registry: {e}") from e
    
    def _save_registry(self, data: Dict) -> None:
        content = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        atomic_write(str(self.registry_path), content)
    
    def _validate_script_id(self, script_id: str) -> Optional[str]:
        """Validate script identifier.
        
        Args:
            script_id: Script identifier to validate
            
        Returns:
            Error message if validation fails, None if valid
        """
        if not script_id:
            return "Script ID cannot be empty"
        
        if len(script_id) > 100:
            return "Script ID cannot exceed 100 characters"
        
        # Check for reserved words
        reserved_words = ['airflow', 'dag', 'task', 'kharon', 'operator', 'sensor']
        if script_id.lower() in reserved_words:
            return f"Script ID cannot be reserved word: {script_id}"
        
        return None
    
    def _build_dag_id(self, client_id: str, script_name: str) -> str:
        with self._lock:
            raw = f"{client_id}_{script_name}"
            base = self._sanitize_script_id(raw)
            registry = self._load_registry()
            if base not in registry:
                return base
            n = 2
            while f"{base}_{n}" in registry:
                n += 1
            return f"{base}_{n}"
    
    @staticmethod
    def _sanitize_for_python(value: str) -> str:
        """Escape a string for safe embedding in Python source code."""
        return repr(value)

    def _sanitize_script_id(self, script_id: str) -> str:
        """Sanitize script identifier for DAG naming.
        
        Args:
            script_id: Original script identifier
            
        Returns:
            Sanitized script identifier
        """
        sanitized = script_id.lower()
        
        sanitized = re.sub(r'[^a-z0-9_]', '_', sanitized)
        
        sanitized = re.sub(r'_+', '_', sanitized)
        
        sanitized = sanitized.strip('_')
        
        if sanitized and not sanitized[0].isalpha():
            sanitized = 'script_' + sanitized
        
        return sanitized
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get registry status information.
        
        Returns:
            Dict with registry status information
        """
        try:
            registry_data = self._load_registry()
            return {
                "registry_exists": self.registry_path.exists(),
                "registry_path": str(self.registry_path),
                "total_scripts": len(registry_data),
                "dags_directory": str(self.dags_dir),
                "dags_directory_exists": self.dags_dir.exists(),
                "generated_dags": len(registry_data),
            }
        except Exception as e:
            return {
                "error": str(e),
                "registry_path": str(self.registry_path),
                "dags_directory": str(self.dags_dir),
            }

    def get_all_scripts(self) -> Dict:
        """Return all registered scripts from the registry."""
        with self._lock:
            return self._load_registry()