"""Async client for OCR API."""

from pathlib import Path
from typing import Optional, Union

import httpx
import json

from abrege_sdk.schemas.health import Health
from abrege_sdk.schemas.task import TaskModel, TaskStatus
from abrege_sdk.schemas.content import Input
from abrege_sdk.schemas.parameters import SummaryParameters
from abrege_sdk.exceptions import AbregeAPIError, AbregeTimeoutError


class SyncAbregeClient:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    def __enter__(self):
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            self._client.close()

    def _ensure_client(self):
        if self._client is None:
            raise RuntimeError(
                "Client not initialized. Use 'with SyncAbregeClient(...) as client:'"
            )

    def _request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        self._ensure_client()
        try:
            response = self._client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            raise AbregeTimeoutError(f"Request timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise AbregeAPIError(
                status_code=e.response.status_code,
                message=e.response.text,
            )

    def get_health(self) -> Health:
        response = self._request("GET", "/api/health")
        return Health(**response.json())

    def summarize_doc(
        self,
        file_path: Union[str, Path],
        prompt: Optional[str] = None,
        parameters: Optional[SummaryParameters] = None,
        extras: Optional[dict] = None,
    ) -> TaskModel:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            files = {
                "file": (file_path.name, f),
            }
            data = {}
            if prompt is not None:
                data["prompt"] = prompt
            if parameters is not None:
                data["parameters"] = parameters.model_dump_json()
            if extras is not None:
                data["extras"] = json.dumps(extras)

            response = self._request(
                "POST",
                "/api/task/document",
                files=files,
                data=data,
            )
        return TaskModel(**response.json())

    def summarize_text(
        self,
        input: Input,
    ) -> TaskModel:
        data = {
            "input": input.model_dump_json(),
        }

        response = self._request(
            "POST",
            "/api/task/text-url",
            data=data,
        )
        return TaskModel(**response.json())

    def get_task(self, task_id: str) -> TaskModel:
        response = self._request("GET", f"/api/tasks/{task_id}")
        return TaskModel(**response.json())

    def get_task_text(self, task_id: str) -> str:
        response = self._request("GET", f"/api/text-task/{task_id}")
        return response.text

    def wait_for_task(
        self,
        task_id: str,
        poll_interval: float = 2.0,
        max_wait_time: float = 300.0,
    ) -> TaskModel:
        import time
        elapsed = 0.0
        while elapsed < max_wait_time:
            task = self.get_task(task_id)
            if task.status == TaskStatus.COMPLETED.value:
                return task
            elif task.status == TaskStatus.FAILED.value:
                error = (
                    task.extras.get("error", "Unknown error")
                    if task.extras
                    else "Unknown error"
                )
                raise AbregeAPIError(500, f"Task failed: {error}")
            time.sleep(poll_interval)
            elapsed += poll_interval
        raise AbregeTimeoutError(
            f"Task {task_id} did not complete within {max_wait_time}s"
        )
