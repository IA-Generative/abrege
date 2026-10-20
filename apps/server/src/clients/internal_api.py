import os
import random
import time
from typing import Callable

import httpx

from src.utils.logger import logger_abrege

ABREGE_API_BASE_URL = os.environ.get("ABREGE_API_BASE_URL", "http://abrege_api:5000")
INTERNAL_SERVICE_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN")


# The save routes replace a chunk's rows (idempotent), so a retried POST can never duplicate data.
# Only transient failures are retried: transport errors (timeout, connection refused/reset while
# the api restarts or is rolling out) and 429/502/503/504. Client errors (401, 404, 422…) will not
# get better by retrying and surface immediately.
RETRYABLE_STATUS = frozenset({429, 502, 503, 504})
DEFAULT_RETRY_DELAYS = (1.0, 3.0, 8.0)


class InternalApiClient:
    """HTTP client the worker uses to persist Q&A/entities/relationships through the API's
    internal CRUD routes, instead of writing to the database directly."""

    def __init__(
        self,
        base_url: str = ABREGE_API_BASE_URL,
        token: str | None = INTERNAL_SERVICE_TOKEN,
        timeout: float = 30.0,
        retry_delays: tuple[float, ...] = DEFAULT_RETRY_DELAYS,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._retry_delays = retry_delays
        self._sleep = sleep
        self._base_url = base_url
        # A short connect timeout: when the api is unreachable (wrong URL/port, network policy), fail
        # fast instead of blocking every chunk for the full request timeout.
        self._client = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(timeout, connect=5.0),
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
        attempts = len(self._retry_delays) + 1
        for attempt in range(1, attempts + 1):
            last = attempt == attempts
            try:
                response = self._client.post(path, json=json_body)
            except httpx.TransportError as e:
                if last:
                    logger_abrege.error(
                        f"Internal API unreachable: POST {self._base_url}{path} -> {type(e).__name__} after {attempts} attempts. "
                        "Check ABREGE_API_BASE_URL: it must reach the api Service (on Kubernetes the Service port, e.g. "
                        "http://abrege-api, not the container port 5000) and no network policy may block worker -> api."
                    )
                    raise
                self._wait_before_retry(path, attempt, attempts, type(e).__name__)
                continue

            if response.status_code in RETRYABLE_STATUS and not last:
                self._wait_before_retry(path, attempt, attempts, f"HTTP {response.status_code}")
                continue
            if response.status_code >= 400:
                logger_abrege.error(f"Internal API call failed: POST {path} -> {response.status_code} {response.text}")
            response.raise_for_status()
            return

    def _wait_before_retry(self, path: str, attempt: int, attempts: int, reason: str) -> None:
        delay = self._retry_delays[attempt - 1] * random.uniform(0.8, 1.2)
        logger_abrege.warning(f"Internal API call POST {path} failed ({reason}), retrying in {delay:.1f}s (attempt {attempt}/{attempts})")
        self._sleep(delay)


internal_api_client = InternalApiClient()
