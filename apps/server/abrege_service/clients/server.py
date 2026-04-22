import requests
from loguru import logger
import os
from src.models.task import TaskModel


class ServerClient:
    def __init__(
        self,
        base_url: str = os.getenv("SERVER_BASE_URL", "http://localhost:5000"),
        headers: dict[str, str] | None = {
            "Authorization": f"Bearer {os.getenv('SERVER_API_KEY', 'secret-api')}",
            "X-User-Id": os.getenv("SERVER_USER_ID", "test_user"),
            "X-Roles": os.getenv("SERVER_USER_ROLES", "admin"),
        },
        blocking: bool = True,
    ):
        self.base_url = base_url
        self.headers = headers or {}
        self.blocking = blocking

    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        method = method.lower()
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)

        if self.blocking:
            logger.debug(f"Request: {response.content}")
            response.raise_for_status()
        return response

    def get_health(self) -> dict:
        response = self.request("GET", "/api/health")
        return response.json()

    def get_task(self, task_id: str) -> dict:
        response = self.request("GET", f"/api/task/{task_id}")
        return response.json()

    def update_task(self, task_id: str, data: dict) -> dict:
        response = self.request("PUT", f"/api/task/{task_id}", json=data)
        return response.json()

    def upsert_chunks(self, chunks: list[dict]) -> list[dict]:
        response = self.request("POST", "/api/v1/chunks/bulk", json={"chunks": chunks})
        return response.json()

    def search_task_by_fields(self, **filters) -> TaskModel | None:
        response = self.request("GET", "/api/task/search", params=filters)
        data = response.json()
        if data:
            return TaskModel.model_validate(data)
        return None
