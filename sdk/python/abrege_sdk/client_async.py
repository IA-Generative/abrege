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
import time
from abrege_sdk.schemas.health import Health
from abrege_sdk.schemas.pagination import Pagination
from abrege_sdk.schemas.task import TaskModel, TaskStatus
from abrege_sdk.schemas.content import Input
from abrege_sdk.schemas.parameters import SummaryParameters
from abrege_sdk.exceptions import AbregeAPIError, AbregeAuthenticationError, AbregeTimeoutError

# Refresh proactively before actual expiry, so a request never races a token that
# expires mid-flight - same skew the BFF session store uses server-side.
_TOKEN_REFRESH_SKEW_SECONDS = 30


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

        # Only populated by `login()`/`refresh_access_token()` - a static `api_key`
        # has no refresh token to renew, so auto-refresh stays a no-op for it.
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        self.refresh_token_expires_at: Optional[float] = None

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
        _skip_auth_refresh: bool = False,
        **kwargs,
    ) -> httpx.Response:
        """Make an HTTP request."""
        self._ensure_client()
        if not _skip_auth_refresh:
            await self._ensure_fresh_token()

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

    def _apply_token_response(self, data: dict) -> None:
        self.api_key = data["access_token"]
        self.token_expires_at = time.time() + data["expires_in"]
        if "refresh_token" in data:
            self.refresh_token = data["refresh_token"]
        if "refresh_expires_in" in data:
            self.refresh_token_expires_at = time.time() + data["refresh_expires_in"]
        if self._client is not None:
            self._client.headers["Authorization"] = f"Bearer {self.api_key}"

    async def _ensure_fresh_token(self) -> None:
        """Proactively refresh the access token before it expires, mirroring how the
        BFF refreshes browser sessions server-side (`SessionStore.ensure_fresh`). A
        no-op unless `login()`/`refresh_access_token()` populated `refresh_token`."""
        if self.refresh_token is None or self.token_expires_at is None:
            return
        if time.time() < self.token_expires_at - _TOKEN_REFRESH_SKEW_SECONDS:
            return
        if self.refresh_token_expires_at is not None and time.time() >= self.refresh_token_expires_at:
            raise AbregeAuthenticationError("Refresh token expired - call login() again.")
        await self.refresh_access_token()

    async def login(self, username: str, password: str) -> None:
        """Authenticate with a Keycloak username/password, and use the resulting
        access token for subsequent requests instead of `api_key`.

        Calls this API's own `POST /api/auth/token`, which performs the Keycloak
        exchange server-side (the client secret never leaves the backend, and the
        SDK never talks to Keycloak directly). Requires the Keycloak client to have
        "Direct Access Grants" enabled.

        The response also carries a refresh token, which subsequent requests use to
        transparently renew the access token as it approaches expiry - see
        `refresh_access_token()`.

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

        self._apply_token_response(response.json())

    async def refresh_access_token(self) -> None:
        """Exchange the current `refresh_token` for a fresh access token, via this
        API's `POST /api/auth/refresh` (same server-side trust boundary as `login()`).

        Called automatically before a request if the access token is near expiry -
        call it directly only to force an early renewal.

        Raises:
            AbregeAuthenticationError: If there is no refresh token to use, or the
                server rejects it (e.g. expired/revoked).
        """
        if self.refresh_token is None:
            raise AbregeAuthenticationError("No refresh token available - call login() first.")

        try:
            response = await self._request(
                "POST",
                "/api/auth/refresh",
                json={"refresh_token": self.refresh_token},
                _skip_auth_refresh=True,
            )
        except AbregeAPIError as e:
            raise AbregeAuthenticationError(f"Token refresh failed: {e.message}")

        self._apply_token_response(response.json())

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
