"""
ScriptMonitor class for health tracking and execution history.

Provides comprehensive monitoring of script execution with health metrics,
alert rules evaluation, and persistent history tracking.
"""

import dataclasses
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .constants import MONITORING_DIR, MAX_HISTORY_ENTRIES

logger = logging.getLogger("kharon.monitor")


@dataclasses.dataclass
class ScriptHealth:
    """
    Health metrics for a script based on execution history.
    
    Attributes:
        script_id: Unique identifier for the script
        total_executions: Total number of executions recorded
        success_count: Number of successful executions
        failure_count: Number of failed executions
        success_rate: Ratio of successful executions (0.0 to 1.0)
        consecutive_failures: Number of consecutive failed executions
        last_execution_time: Timestamp of last execution (ISO format)
        last_status: Status of last execution ('success' or 'failed')
        is_healthy: Whether script is currently healthy based on thresholds
    """
    script_id: str
    total_executions: int
    success_count: int
    failure_count: int
    success_rate: float
    consecutive_failures: int
    last_execution_time: Optional[str]
    last_status: Optional[str]
    is_healthy: bool


@dataclasses.dataclass
class AlertRule:
    """
    Alert rule definition for monitoring script health.
    
    Attributes:
        alert_type: Type of alert (e.g., 'success_rate', 'consecutive_failures')
        condition: Comparison condition (e.g., '<', '>', '==')
        threshold: Threshold value for triggering alert
        enabled: Whether rule is active
    """
    alert_type: str
    condition: str
    threshold: float
    enabled: bool


class ScriptMonitor:
    """
    Comprehensive script monitoring and health tracking system.
    
    Manages execution history, calculates health metrics, and evaluates
    alert rules for script health monitoring.
    """
    
    def __init__(self, monitoring_dir: Optional[str] = None):
        """
        Initialize the script monitor.
        
        Args:
            monitoring_dir: Directory to store monitoring data (defaults to MONITORING_DIR)
        """
        self.monitoring_dir = Path(monitoring_dir) if monitoring_dir else MONITORING_DIR
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        
    def record_execution(
        self, 
        script_id: str, 
        status: str, 
        exit_code: int, 
        duration: float, 
        stdout: str, 
        stderr: str, 
        attempt: int = 1, 
        timeout_occurred: bool = False
    ) -> None:
        """
        Record script execution in monitoring history.
        
        Args:
            script_id: Unique identifier for the script
            status: Execution status ('success' or 'failed')
            exit_code: Exit code from script execution
            duration: Duration of execution in seconds
            stdout: Complete stdout output
            stderr: Complete stderr output
            attempt: Attempt number (1 for first attempt)
            timeout_occurred: Whether execution timed out
        """
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'exit_code': exit_code,
            'duration_seconds': duration,
            'attempt': attempt,
            'timeout_occurred': timeout_occurred,
            'stdout_preview': stdout[:500] if stdout else "",
            'stderr_preview': stderr[:500] if stderr else ""
        }
        
        history = self._load_history(script_id)
        
        history.append(history_entry)
        
        if len(history) > MAX_HISTORY_ENTRIES:
            history = history[-MAX_HISTORY_ENTRIES:]
            
        self._save_history(script_id, history)
        
        logger.info(f"Recorded execution for {script_id}: {status}")
        
    def get_script_health(self, script_id: str) -> ScriptHealth:
        """
        Calculate health metrics for a script based on execution history.
        
        Args:
            script_id: Unique identifier for the script
            
        Returns:
            ScriptHealth object with calculated metrics
        """
        history = self._load_history(script_id)
        
        if not history:
            return ScriptHealth(
                script_id=script_id,
                total_executions=0,
                success_count=0,
                failure_count=0,
                success_rate=0.0,
                consecutive_failures=0,
                last_execution_time=None,
                last_status=None,
                is_healthy=True
            )
        
        total_executions = len(history)
        success_count = sum(1 for entry in history if entry['status'] == 'success')
        failure_count = total_executions - success_count
        success_rate = success_count / total_executions if total_executions > 0 else 0.0
        
        consecutive_failures = 0
        for entry in reversed(history):
            if entry['status'] == 'failed':
                consecutive_failures += 1
            else:
                break
        
        last_entry = history[-1]
        last_execution_time = last_entry['timestamp']
        last_status = last_entry['status']
        
        is_healthy = success_rate >= 0.8 and consecutive_failures <= 3
        
        return ScriptHealth(
            script_id=script_id,
            total_executions=total_executions,
            success_count=success_count,
            failure_count=failure_count,
            success_rate=success_rate,
            consecutive_failures=consecutive_failures,
            last_execution_time=last_execution_time,
            last_status=last_status,
            is_healthy=is_healthy
        )
        
    def get_history(self, script_id: str, limit: int = 50) -> List[Dict]:
        """
        Get execution history for a script.
        
        Args:
            script_id: Unique identifier for the script
            limit: Maximum number of entries to return
            
        Returns:
            List of execution history entries
        """
        history = self._load_history(script_id)
        return history[-limit:] if limit else history
        
    def evaluate_rules(self, script_id: str, rules: List[Dict]) -> List[Dict]:
        """
        Evaluate alert rules against script health and latest execution.
        
        Args:
            script_id: Unique identifier for the script
            rules: List of alert rule dictionaries
            
        Returns:
            List of triggered alerts
        """
        health = self.get_script_health(script_id)
        history = self._load_history(script_id)
        triggered_alerts = []
        
        if not history:
            return triggered_alerts
            
        latest_entry = history[-1]
        
        for rule in rules:
            if not rule.get('enabled', True):
                continue
                
            alert_type = rule.get('alert_type')
            condition = rule.get('condition')
            threshold = rule.get('threshold')
            
            if alert_type == 'success_rate':
                value = health.success_rate
            elif alert_type == 'consecutive_failures':
                value = health.consecutive_failures
            elif alert_type == 'execution_time':
                value = latest_entry.get('duration_seconds', 0)
            else:
                continue
                
            alert_triggered = False
            if condition == '>' and value > threshold:
                alert_triggered = True
            elif condition == '<' and value < threshold:
                alert_triggered = True
            elif condition == '==' and value == threshold:
                alert_triggered = True
            elif condition == '>=' and value >= threshold:
                alert_triggered = True
            elif condition == '<=' and value <= threshold:
                alert_triggered = True
                
            if alert_triggered:
                triggered_alerts.append({
                    'rule_type': alert_type,
                    'condition': condition,
                    'threshold': threshold,
                    'value': value,
                    'script_id': script_id,
                    'timestamp': datetime.now().isoformat()
                })
                
        return triggered_alerts
        
    def _load_history(self, script_id: str) -> List[Dict]:
        """
        Load execution history from JSON file.
        
        Args:
            script_id: Unique identifier for the script
            
        Returns:
            List of execution history entries
        """
        history_path = self._history_path(script_id)
        
        if not history_path.exists():
            return []
            
        try:
            with open(history_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load history for {script_id}: {e}")
            return []
            
    def _save_history(self, script_id: str, history: List[Dict]) -> None:
        """
        Save execution history to JSON file.
        
        Args:
            script_id: Unique identifier for the script
            history: List of execution history entries to save
        """
        history_path = self._history_path(script_id)
        
        try:
            with open(history_path, 'w') as f:
                json.dump(history, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save history for {script_id}: {e}")
            
    def _history_path(self, script_id: str) -> Path:
        """
        Get the file path for script history.
        
        Args:
            script_id: Unique identifier for the script
            
        Returns:
            Path to the history JSON file
        """
        return self.monitoring_dir / f"{script_id}_history.json"