"""Async client for Abrège API.

Example (static API key, e.g. a Keycloak service-account token):
    >>> async with AsyncAbregeClient("http://localhost:5000", api_key="...") as client:
    ...     task = await client.summarize_text(Input(text="..."))

Example (Keycloak username/password - real user identity):
    >>> async with AsyncAbregeClient("http://localhost:5000") as client:
    ...     await client.login("user@example.com", "hunter2")
    ...     task = await client.summarize_text(Input(text="..."))
"""

from pathlib import Path
from typing import Optional, Union

import httpx
import json
import asyncio
from abrege_sdk.schemas.health import Health
from abrege_sdk.schemas.pagination import Pagination
from abrege_sdk.schemas.task import TaskModel, TaskStatus
from abrege_sdk.schemas.content import Input
from abrege_sdk.schemas.parameters import SummaryParameters
from abrege_sdk.exceptions import AbregeAPIError, AbregeAuthenticationError, AbregeTimeoutError


class AsyncAbregeClient:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize the async Abrège client.

        Args:
            base_url: Base URL of the Abrège API (e.g., "http://localhost:5000")
            api_key: Optional static bearer token for authentication (a Keycloak
                access/service token - mutually exclusive with `login()`, whichever
                sets the `Authorization` header last wins)
            timeout: Default timeout for requests in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _ensure_client(self):
        """Ensure client is initialized."""
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with AsyncOCRClient(...) as client:'")

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> httpx.Response:
        """Make an HTTP request."""
        self._ensure_client()

        try:
            response = await self._client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            raise AbregeTimeoutError(f"Request timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise AbregeAPIError(
                status_code=e.response.status_code,
                message=e.response.text,
            )

    async def login(self, username: str, password: str) -> None:
        """Authenticate with a Keycloak username/password, and use the resulting
        access token for subsequent requests instead of `api_key`.

        Calls this API's own `POST /api/auth/token`, which performs the Keycloak
        exchange server-side (the client secret never leaves the backend, and the
        SDK never talks to Keycloak directly). Requires the Keycloak client to have
        "Direct Access Grants" enabled.

        Args:
            username: Keycloak username (or email, depending on realm config)
            password: Keycloak password

        Raises:
            AbregeAuthenticationError: If the credentials are rejected
        """
        try:
            response = await self._request(
                "POST",
                "/api/auth/token",
                json={"username": username, "password": password},
            )
        except AbregeAPIError as e:
            raise AbregeAuthenticationError(f"Login failed: {e.message}")

        self.api_key = response.json()["access_token"]
        if self._client is not None:
            self._client.headers["Authorization"] = f"Bearer {self.api_key}"

    async def get_health(self) -> Health:
        response = await self._request("GET", "/api/health")
        return Health(**response.json())

    async def summarize_doc(
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

            response = await self._request(
                "POST",
                "/api/task/document",
                files=files,
                data=data,
            )
        return TaskModel(**response.json())

    async def summarize_text(
        self,
        input: Input,
    ) -> TaskModel:
        data = {
            "input": input.model_dump_json(),
        }

        response = await self._request(
            "POST",
            "/api/task/text-url",
            data=data,
        )
        return TaskModel(**response.json())

    async def get_task(self, task_id: str) -> TaskModel:
        response = await self._request("GET", f"/api/task/{task_id}")
        return TaskModel(**response.json())

    async def get_task_text(self, task_id: str) -> str:
        """Convenience wrapper around `get_task`: there is no dedicated
        "text" endpoint on this API - the summarized text is a field on the task's
        own output. Returns an empty string until the task has produced one."""
        task = await self.get_task(task_id)
        return getattr(task.output, "summary", "") or ""

    async def get_user_tasks(self, page: int = 1, page_size: int = 10) -> Pagination[TaskModel]:
        """Get a page of tasks belonging to the authenticated user.

        Args:
            page: Page number (1-indexed)
            page_size: Number of tasks per page

        Returns:
            Paginated list of TaskModel objects (``total``/``page``/``page_size``/``items``)
        """
        response = await self._request(
            "GET",
            "/api/task/user/",
            params={"offset": page, "limit": page_size},
        )
        return Pagination[TaskModel](**response.json())

    async def cancel_task(self, task_id: str) -> TaskModel:
        """Cancel a queued/running task.

        Args:
            task_id: Task ID

        Returns:
            The updated TaskModel (status ``canceled``)
        """
        response = await self._request("POST", f"/api/task/{task_id}/cancel")
        return TaskModel(**response.json())

    async def delete_task(self, task_id: str) -> None:
        """Delete a finished task (and its stored result) by ID. The task must not
        be active - cancel it first.

        Args:
            task_id: Task ID
        """
        await self._request("DELETE", f"/api/task/{task_id}")

    async def wait_for_task(
        self,
        task_id: str,
        poll_interval: float = 2.0,
        max_wait_time: float = 300.0,
    ) -> TaskModel:
        elapsed = 0.0
        while elapsed < max_wait_time:
            task = await self.get_task(task_id)
            if task.status == TaskStatus.COMPLETED.value:
                return task
            elif task.status == TaskStatus.FAILED.value:
                error = task.extras.get("error", "Unknown error") if task.extras else "Unknown error"
                raise AbregeAPIError(500, f"Task failed: {error}")
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        raise AbregeTimeoutError(f"Task {task_id} did not complete within {max_wait_time}s")
