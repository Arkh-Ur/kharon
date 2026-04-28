"""Airflow REST API client for Kharōn webapp (Airflow 3.x compatible).

Uses JWT cookie-based auth via /api/v2/auth/login flow.
"""

import json
from typing import Dict, List, Optional, Any
import requests
from requests.auth import HTTPBasicAuth
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
        self.session.timeout = 30
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        self._authenticate()

    def _authenticate(self) -> None:
        login_url = f"{self.base_url}/api/v2/auth/login"
        try:
            response = self.session.get(
                login_url,
                auth=HTTPBasicAuth(self.username, self.password),
                allow_redirects=True,
            )
            if '_token' not in self.session.cookies.get_dict():
                raise AirflowClientError(
                    "Authentication failed: no JWT token received from Airflow",
                    status_code=response.status_code,
                )
        except RequestException as e:
            raise AirflowClientError(f"Auth request failed: {str(e)}") from e

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        url = f"{self.base_url}{endpoint}"

        if '_token' not in self.session.cookies.get_dict():
            self._authenticate()

        try:
            response = self.session.request(method, url, **kwargs)

            if response.status_code == 401:
                self._authenticate()
                response = self.session.request(method, url, **kwargs)

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
            if isinstance(e, AirflowClientError):
                raise
            raise AirflowClientError(f"Request failed: {str(e)}") from e

    def health_check(self) -> Dict:
        return self._request("GET", f"{self.API_PREFIX}/monitor/health")

    def list_dags(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        endpoint = f"{self.API_PREFIX}/dags"
        params = {"limit": limit, "offset": offset}

        try:
            response = self._request("GET", endpoint, params=params)
            return response.get("dags", [])
        except AirflowClientError:
            raise

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
            response = self.session.request("GET", f"{self.base_url}{endpoint}")
            if not response.ok:
                try:
                    err = response.json()
                    detail = err.get("detail") or err.get("title") or response.text[:200]
                except Exception:
                    detail = response.text[:200]
                raise AirflowClientError(
                    f"Log no disponible (HTTP {response.status_code}): {detail}",
                    status_code=response.status_code,
                )
            # Airflow 3.x: {"content": <list|str>, "continuation_token": ...}
            try:
                data = response.json()
                if isinstance(data, dict) and "content" in data:
                    return format_airflow_log(data["content"])
            except (ValueError, json.JSONDecodeError):
                pass
            return response.text
        except RequestException as exc:
            if isinstance(exc, AirflowClientError):
                raise
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
