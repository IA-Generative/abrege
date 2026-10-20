from typing import Any, Callable

import openai
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI


class PerCallRunnable:
    """Builds a fresh LLM client, with its own HTTP client, for every call and closes it afterwards.

    Celery tasks run each coroutine with `asyncio.run`, which opens and closes a new event loop.
    langchain_openai shares one cached httpx client (`lru_cache`) between every ChatOpenAI instance, so
    its pooled keep-alive connections stay bound to the loop of an earlier task and the next call
    fails with "Event loop is closed" (surfacing as a spurious `Connection error`). Giving each call
    its own `http_async_client`, created inside the running loop, avoids ever reusing a dead one.
    """

    def __init__(
        self,
        build: Callable[[ChatOpenAI], Runnable],
        make_llm: Callable[[Any], ChatOpenAI],
        make_http_client: Callable[[], Any] = openai.DefaultAsyncHttpxClient,
    ):
        self._build = build
        self._make_llm = make_llm
        self._make_http_client = make_http_client

    async def ainvoke(self, input: Any, *args: Any, **kwargs: Any) -> Any:
        http_client = self._make_http_client()
        try:
            return await self._build(self._make_llm(http_client)).ainvoke(input, *args, **kwargs)
        finally:
            await http_client.aclose()
