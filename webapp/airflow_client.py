"""
Airflow REST API client for Kharōn webapp.

Provides methods to interact with Airflow API for DAG management and monitoring.
"""

import json
from typing import Dict, List, Optional, Any
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from .config import config


class AirflowClientError(Exception):
    """Custom exception for Airflow API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        """Initialize AirflowClientError.
        
        Args:
            message: Error message
            status_code: HTTP status code if available
            response: Full response dict if available
        """
        super().__init__(message)
        self.status_code = status_code
        self.response = response
        
    def __str__(self) -> str:
        """String representation of the error."""
        base_msg = super().__str__()
        if self.status_code:
            base_msg += f" (HTTP {self.status_code})"
        if self.response:
            base_msg += f" - Response: {json.dumps(self.response, indent=2)}"
        return base_msg


class AirflowClient:
    """Airflow REST API client."""
    
    def __init__(self, base_url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        """Initialize AirflowClient.
        
        Args:
            base_url: Airflow base URL. If None, uses config.AIRFLOW_BASE_URL
            username: Airflow username. If None, uses config.AIRFLOW_USER
            password: Airflow password. If None, uses config.AIRFLOW_PASSWORD
        """
        self.base_url = base_url or config.AIRFLOW_BASE_URL
        self.username = username or config.AIRFLOW_USER
        self.password = password or config.AIRFLOW_PASSWORD
        
        # Create session with Basic Auth and timeout
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.username, self.password)
        self.session.timeout = 30
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make unified HTTP request to Airflow API.
        
        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            endpoint: API endpoint path (e.g., '/health')
            **kwargs: Additional request parameters
            
        Returns:
            JSON response as dict
            
        Raises:
            AirflowClientError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Handle non-successful responses
            if not response.ok:
                try:
                    error_data = response.json()
                except (ValueError, json.JSONDecodeError):
                    error_data = {"error": response.text}
                
                raise AirflowClientError(
                    f"Request failed: {response.status_code} {response.reason}",
                    status_code=response.status_code,
                    response=error_data
                )
            
            # Parse JSON response
            return response.json()
            
        except RequestException as e:
            raise AirflowClientError(f"Request failed: {str(e)}") from e
    
    def health_check(self) -> Dict:
        """Check Airflow API health status.
        
        Returns:
            Health check response dict
            
        Raises:
            AirflowClientError: If health check fails
        """
        return self._request("GET", "/health")
    
    def list_dags(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List all DAGs.
        
        Args:
            limit: Maximum number of DAGs to return
            offset: Offset for pagination
            
        Returns:
            List of DAG dictionaries
            
        Raises:
            AirflowClientError: If request fails
        """
        endpoint = "/api/v1/dags"
        params = {"limit": limit, "offset": offset}
        
        try:
            response = self._request("GET", endpoint, params=params)
            return response.get("dags", [])
        except AirflowClientError:
            raise
    
    def get_dag(self, dag_id: str) -> Dict:
        """Get a specific DAG.
        
        Args:
            dag_id: The DAG identifier
            
        Returns:
            DAG dictionary
            
        Raises:
            AirflowClientError: If request fails
        """
        endpoint = f"/api/v1/dags/{dag_id}"
        
        try:
            return self._request("GET", endpoint)
        except AirflowClientError:
            raise
    
    def trigger_dag(self, dag_id: str, conf: Optional[Dict] = None) -> Dict:
        """Trigger a DAG run.
        
        Args:
            dag_id: The DAG identifier
            conf: Optional configuration for the DAG run
            
        Returns:
            Trigger response dictionary
            
        Raises:
            AirflowClientError: If request fails
        """
        endpoint = f"/api/v1/dags/{dag_id}/dagRuns"
        data = {"conf": conf} if conf else {}
        
        try:
            return self._request("POST", endpoint, json=data)
        except AirflowClientError:
            raise
    
    def list_dag_runs(self, dag_id: str, limit: int = 50, state: Optional[str] = None) -> List[Dict]:
        """List DAG runs for a specific DAG.
        
        Args:
            dag_id: The DAG identifier
            limit: Maximum number of runs to return
            state: Filter by state (e.g., 'running', 'success', 'failed')
            
        Returns:
            List of DAG run dictionaries
            
        Raises:
            AirflowClientError: If request fails
        """
        endpoint = f"/api/v1/dags/{dag_id}/dagRuns"
        params = {"limit": limit}
        
        if state:
            params["state"] = state
            
        try:
            response = self._request("GET", endpoint, params=params)
            return response.get("dag_runs", [])
        except AirflowClientError:
            raise
    
    def get_dag_run(self, dag_id: str, dag_run_id: str) -> Dict:
        """Get a specific DAG run.
        
        Args:
            dag_id: The DAG identifier
            dag_run_id: The DAG run identifier
            
        Returns:
            DAG run dictionary
            
        Raises:
            AirflowClientError: If request fails
        """
        endpoint = f"/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}"
        
        try:
            return self._request("GET", endpoint)
        except AirflowClientError:
            raise
    
    def list_task_instances(self, dag_id: str, dag_run_id: str) -> List[Dict]:
        """List task instances for a DAG run.
        
        Args:
            dag_id: The DAG identifier
            dag_run_id: The DAG run identifier
            
        Returns:
            List of task instance dictionaries
            
        Raises:
            AirflowClientError: If request fails
        """
        endpoint = f"/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances"
        
        try:
            response = self._request("GET", endpoint)
            return response.get("task_instances", [])
        except AirflowClientError:
            raise
    
    def get_task_log(self, dag_id: str, dag_run_id: str, task_id: str, try_number: int = 1) -> str:
        """Get task execution log.
        
        Args:
            dag_id: The DAG identifier
            dag_run_id: The DAG run identifier
            task_id: The task identifier
            try_number: The try number for the task
            
        Returns:
            Task log as string
            
        Raises:
            AirflowClientError: If request fails
        """
        endpoint = f"/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/log"
        params = {"try_number": try_number}
        
        try:
            response = self._request("GET", endpoint, params=params)
            return response.get("log", "")
        except AirflowClientError:
            raise
    
    def pause_dag(self, dag_id: str, paused: bool = True) -> Dict:
        """Pause or unpause a DAG.
        
        Args:
            dag_id: The DAG identifier
            paused: True to pause, False to unpause
            
        Returns:
            Update response dictionary
            
        Raises:
            AirflowClientError: If request fails
        """
        endpoint = f"/api/v1/dags/{dag_id}"
        data = {"is_paused": paused}
        
        try:
            return self._request("PATCH", endpoint, json=data)
        except AirflowClientError:
            raise