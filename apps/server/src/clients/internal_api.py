import os

import httpx

from src.utils.logger import logger_abrege

ABREGE_API_BASE_URL = os.environ.get("ABREGE_API_BASE_URL", "http://abrege_api:5000")
INTERNAL_SERVICE_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN")


class InternalApiClient:
    """HTTP client the worker uses to persist Q&A/entities/relationships through the API's
    internal CRUD routes, instead of writing to the database directly."""

    def __init__(self, base_url: str = ABREGE_API_BASE_URL, token: str | None = INTERNAL_SERVICE_TOKEN, timeout: float = 30.0):
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={"X-Internal-Token": token} if token else {},
        )

    def save_chunk_qa_items(self, task_id: str, chunk_index: int, qa_items: list[dict], model_name: str | None = None) -> None:
        self._post(f"/api/task/{task_id}/qa", {"chunk_index": chunk_index, "qa_items": qa_items, "model_name": model_name})

    def save_chunk_entities(
        self,
        task_id: str,
        chunk_index: int,
        entities: list[dict],
        relationships: list[dict],
        model_name: str | None = None,
    ) -> None:
        self._post(
            f"/api/task/{task_id}/entities",
            {"chunk_index": chunk_index, "entities": entities, "relationships": relationships, "model_name": model_name},
        )

    def save_global_relationships(
        self, task_id: str, entity_ids_in_order: list[str], relationships: list[dict], model_name: str | None = None
    ) -> None:
        self._post(
            f"/api/task/{task_id}/relationships/global",
            {"entity_ids_in_order": entity_ids_in_order, "relationships": relationships, "model_name": model_name},
        )

    def save_topics(self, task_id: str, topics: list[dict], model_name: str | None = None) -> None:
        self._post(f"/api/task/{task_id}/topics", {"topics": topics, "model_name": model_name})

    def save_chunks(
        self, task_id: str, chunk_index: int, page: int | None, chunks: list[str], model_name: str | None = None
    ) -> None:
        self._post(
            f"/api/task/{task_id}/chunks",
            {"chunk_index": chunk_index, "page": page, "chunks": chunks, "model_name": model_name},
        )

    def _post(self, path: str, json_body: dict) -> None:
        response = self._client.post(path, json=json_body)
        if response.status_code >= 400:
            logger_abrege.error(f"Internal API call failed: POST {path} -> {response.status_code} {response.text}")
        response.raise_for_status()


internal_api_client = InternalApiClient()
