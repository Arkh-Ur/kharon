"""Airflow REST API client for Kharōn webapp (Airflow 3.x compatible).

Uses JWT cookie-based auth via /api/v2/auth/login flow.
"""

import json
from typing import Dict, List, Optional, Any
import requests
from requests.exceptions import RequestException

import config


class AirflowClientError(Exception):

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.status_code:
            base_msg += f" (HTTP {self.status_code})"
        if self.response:
            base_msg += f" - Response: {json.dumps(self.response, indent=2)}"
        return base_msg


class AirflowClient:

    API_PREFIX = "/api/v2"

    def __init__(self, base_url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        self.base_url = base_url or config.AIRFLOW_BASE_URL
        self.username = username or config.AIRFLOW_USER
        self.password = password or config.AIRFLOW_PASSWORD

        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        self._authenticate()

    def _authenticate(self) -> None:
        # This Airflow installation uses GET + BasicAuth for the login endpoint.
        # POST with JSON body returns 405 on this deployment (non-standard but functional).
        from requests.auth import HTTPBasicAuth
        login_url = f"{self.base_url}/api/v2/auth/login"
        try:
            response = self.session.get(
                login_url,
                auth=HTTPBasicAuth(self.username, self.password),
                allow_redirects=True,
                timeout=30,
            )
            if not response.ok or not self.session.cookies:
                raise AirflowClientError(
                    "Authentication failed: no session cookie received",
                    status_code=response.status_code,
                )
        except RequestException as e:
            raise AirflowClientError(f"Auth request failed: {str(e)}") from e

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        url = f"{self.base_url}{endpoint}"

        if not self.session.cookies:
            self._authenticate()

        try:
            response = self.session.request(method, url, timeout=30, **kwargs)

            if response.status_code == 401:
                self._authenticate()
                response = self.session.request(method, url, timeout=30, **kwargs)

            if not response.ok:
                try:
                    error_data = response.json()
                except (ValueError, json.JSONDecodeError):
                    error_data = {"error": response.text}

                raise AirflowClientError(
                    f"Request failed: {response.status_code} {response.reason}",
                    status_code=response.status_code,
                    response=error_data,
                )

            if response.text.strip():
                return response.json()
            return {}

        except RequestException as e:
            raise AirflowClientError(f"Request failed: {str(e)}") from e

    def health_check(self) -> Dict:
        return self._request("GET", f"{self.API_PREFIX}/monitor/health")

    def list_dags(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        endpoint = f"{self.API_PREFIX}/dags"
        all_dags: List[Dict] = []
        current_offset = offset
        max_pages = 20

        for _ in range(max_pages):
            params = {"limit": limit, "offset": current_offset}
            try:
                response = self._request("GET", endpoint, params=params)
                dags = response.get("dags", [])
                all_dags.extend(dags)
                if len(dags) < limit:
                    break
                current_offset += limit
            except AirflowClientError:
                raise

        return all_dags

    def get_dag(self, dag_id: str) -> Dict:
        endpoint = f"{self.API_PREFIX}/dags/{dag_id}"

        try:
            return self._request("GET", endpoint)
        except AirflowClientError:
            raise

    def trigger_dag(self, dag_id: str, conf: Optional[Dict] = None) -> Dict:
        from datetime import datetime, timezone
        endpoint = f"{self.API_PREFIX}/dags/{dag_id}/dagRuns"
        data = {
            "logical_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if conf:
            data["conf"] = conf

        try:
            return self._request("POST", endpoint, json=data)
        except AirflowClientError:
            raise

    def list_dag_runs(self, dag_id: str, limit: int = 50, state: Optional[str] = None) -> List[Dict]:
        endpoint = f"{self.API_PREFIX}/dags/{dag_id}/dagRuns"
        params = {"limit": limit}

        if state:
            params["state"] = state

        try:
            response = self._request("GET", endpoint, params=params)
            return response.get("dag_runs", [])
        except AirflowClientError:
            raise

    def get_dag_run(self, dag_id: str, dag_run_id: str) -> Dict:
        endpoint = f"{self.API_PREFIX}/dags/{dag_id}/dagRuns/{dag_run_id}"

        try:
            return self._request("GET", endpoint)
        except AirflowClientError:
            raise

    def list_task_instances(self, dag_id: str, dag_run_id: str) -> List[Dict]:
        endpoint = f"{self.API_PREFIX}/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances"

        try:
            response = self._request("GET", endpoint)
            return response.get("task_instances", [])
        except AirflowClientError:
            raise

    def get_task_log(self, dag_id: str, dag_run_id: str, task_id: str, try_number: int = 1) -> str:
        from utils import format_airflow_log
        endpoint = (
            f"{self.API_PREFIX}/dags/{dag_id}/dagRuns/{dag_run_id}"
            f"/taskInstances/{task_id}/logs/{try_number}"
        )
        try:
            data = self._request("GET", endpoint)
            if isinstance(data, dict) and "content" in data:
                return format_airflow_log(data["content"])
            return json.dumps(data) if data else ""
        except AirflowClientError:
            raise
        except RequestException as exc:
            raise AirflowClientError(f"Error de red al obtener log: {exc}") from exc

    def pause_dag(self, dag_id: str, paused: bool = True) -> Dict:
        endpoint = f"{self.API_PREFIX}/dags/{dag_id}"
        data = {"is_paused": paused}

        try:
            return self._request("PATCH", endpoint, json=data)
        except AirflowClientError:
            raise

    def delete_dag(self, dag_id: str) -> bool:
        endpoint = f"{self.API_PREFIX}/dags/{dag_id}"
        try:
            self._request("DELETE", endpoint)
            return True
        except AirflowClientError:
            return False
