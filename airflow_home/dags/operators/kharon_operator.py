"""
Custom Airflow operator for Kharōn script orchestration.

Provides a specialized operator for executing external scripts with health monitoring,
timeout handling, and comprehensive error management.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from airflow.sdk.bases.operator import BaseOperator

from utils.constants import DEFAULT_TIMEOUT_SECONDS, DEFAULT_RETRIES
from utils.script_runner import ScriptRunner
from utils.script_monitor import ScriptMonitor
from utils.logger import get_task_logger

logger = get_task_logger(__name__)


class KharonOperator(BaseOperator):
    """
    Custom Airflow operator for executing Kharōn scripts with monitoring.
    
    Executes external scripts with comprehensive error handling, health monitoring,
    and timeout management. Supports both Python and bash scripts with automatic
    detection based on file extension.
    """
    
    template_fields = ('script_path', 'args', 'env_vars')
    
    def __init__(
        self,
        script_path: str,
        script_id: Optional[str] = None,
        client_id: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        retries: int = DEFAULT_RETRIES,
        python: str = "python3",
        skip_if_unhealthy: bool = False,
        max_consecutive_failures: int = 3,
        args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        Initialize the KharonOperator.
        
        Args:
            script_path: Path to the script to execute
            script_id: Unique identifier for the script (derived from filename if not provided)
            client_id: Client identifier for tracking
            timeout: Maximum execution time in seconds
            retries: Number of retry attempts
            python: Python executable to use
            skip_if_unhealthy: Skip execution if script is unhealthy
            max_consecutive_failures: Maximum consecutive failures before skipping
            args: List of arguments to pass to the script
            env_vars: Environment variables to set for script execution
            **kwargs: Additional arguments passed to BaseOperator
        """
        super().__init__(**kwargs)
        self.script_path = script_path
        self.script_id = script_id or self._derive_script_id(script_path)
        self.client_id = client_id
        self.timeout = timeout
        self.retries = retries
        self.python = python
        self.skip_if_unhealthy = skip_if_unhealthy
        self.max_consecutive_failures = max_consecutive_failures
        self.args = args or []
        self.env_vars = env_vars or {}
        
        self.retries = retries
        
        self.monitor = ScriptMonitor()
        self.script_runner = ScriptRunner(timeout=timeout, python=python)
        
    def _derive_script_id(self, script_path: str) -> str:
        """
        Derive script ID from script path filename.
        
        Args:
            script_path: Path to the script file
            
        Returns:
            Script ID (filename without extension)
        """
        return Path(script_path).stem
        
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the script with monitoring and error handling.
        
        Args:
            context: Airflow execution context
            
        Returns:
            Execution result dict
            
        Raises:
            RuntimeError: If script execution fails
        """
        self.log.info(f"Starting script execution: {self.script_path} (ID: {self.script_id})")
        
        if self.skip_if_unhealthy:
            health = self.monitor.get_script_health(self.script_id)
            if (not health.is_healthy and 
                health.consecutive_failures >= self.max_consecutive_failures):
                self.log.warning(
                    f"Skipping execution of {self.script_id} - unhealthy "
                    f"(consecutive_failures={health.consecutive_failures}, "
                    f"max_consecutive_failures={self.max_consecutive_failures})"
                )
                return {
                    'status': 'skipped',
                    'reason': 'unhealthy',
                    'script_id': self.script_id,
                    'consecutive_failures': health.consecutive_failures
                }
        
        try:
            result = self.script_runner.run_script(
                script_path=self.script_path,
                args=self.args,
                env_vars=self.env_vars
            )
            
            # Record execution in monitoring
            self.monitor.record_execution(
                script_id=self.script_id,
                status='success' if result.success else 'failed',
                exit_code=result.exit_code,
                duration=result.duration_seconds,
                stdout=result.stdout,
                stderr=result.stderr,
                timeout_occurred=result.timed_out
            )
            
            xcom_data = {
                'status': 'success' if result.success else 'failed',
                'script_id': self.script_id,
                'duration_seconds': result.duration_seconds,
                'exit_code': result.exit_code
            }
            
            if result.success and result.parsed_result:
                xcom_data['parsed_result'] = result.parsed_result
            
            rules = self._get_monitoring_rules()
            alerts = self.monitor.evaluate_rules(self.script_id, rules)
            
            if alerts:
                self.log.warning(f"Triggered {len(alerts)} monitoring alerts for {self.script_id}")
                for alert in alerts:
                    self.log.warning(f"Alert: {alert}")
            
            if result.success:
                self.log.info(
                    f"Script {self.script_id} completed successfully "
                    f"({result.duration_seconds:.2f}s, exit_code={result.exit_code})"
                )
                return xcom_data
                
            # Handle failed execution
            error_msg = result.stderr if result.stderr else "Unknown error"
            xcom_data['error'] = error_msg
            
            self.log.error(
                f"Script {self.script_id} failed "
                f"({result.duration_seconds:.2f}s, exit_code={result.exit_code}): {error_msg}"
            )
            
            context['ti'].xcom_push(key='return_value', value=xcom_data)
            raise RuntimeError(f"Script execution failed: {error_msg}")
            
        except Exception as e:
            self.monitor.record_execution(
                script_id=self.script_id,
                status='failed',
                exit_code=-1,
                duration=0.0,
                stdout="",
                stderr=str(e),
                timeout_occurred=False
            )
            
            self.log.error(f"Script {self.script_id} execution error: {e}")
            raise
            
    def _get_monitoring_rules(self) -> List[Dict[str, Any]]:
        """
        Get monitoring rules for this script.
        
        Returns:
            List of monitoring rule dictionaries
        """
        rules = [
            {
                'alert_type': 'success_rate',
                'condition': '<',
                'threshold': 0.8,
                'enabled': True
            },
            {
                'alert_type': 'consecutive_failures',
                'condition': '>=',
                'threshold': 3,
                'enabled': True
            },
            {
                'alert_type': 'execution_time',
                'condition': '>',
                'threshold': self.timeout * 0.9,
                'enabled': True
            }
        ]
        
        if self.client_id:
            pass
            
        return rules