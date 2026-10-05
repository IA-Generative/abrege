import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from abrege_service.models.summary.per_call_runnable import PerCallRunnable


def _fake_http_client():
    http_client = MagicMock()
    http_client.aclose = AsyncMock()
    return http_client


def _runnable_returning(value="out"):
    inner = MagicMock()
    inner.ainvoke = AsyncMock(return_value=value)
    return inner


@pytest.mark.asyncio
async def test_each_call_gets_its_own_http_client_and_closes_it():
    http_clients = []

    def make_http_client():
        http_clients.append(_fake_http_client())
        return http_clients[-1]

    llms_built_with = []

    def make_llm(http_client):
        llms_built_with.append(http_client)
        return MagicMock()

    runnable = PerCallRunnable(lambda llm: _runnable_returning(), make_llm, make_http_client)
    assert await runnable.ainvoke({"text": "a"}) == "out"
    assert await runnable.ainvoke({"text": "b"}) == "out"

    assert len(http_clients) == 2
    assert http_clients[0] is not http_clients[1]
    assert llms_built_with == http_clients
    for http_client in http_clients:
        http_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_input_is_forwarded_to_the_built_runnable():
    inner = _runnable_returning()
    runnable = PerCallRunnable(lambda llm: inner, lambda http: MagicMock(), _fake_http_client)

    await runnable.ainvoke({"text": "a"})

    inner.ainvoke.assert_awaited_once_with({"text": "a"})


@pytest.mark.asyncio
async def test_http_client_is_closed_even_when_the_call_fails():
    http_client = _fake_http_client()
    inner = MagicMock()
    inner.ainvoke = AsyncMock(side_effect=RuntimeError("boom"))
    runnable = PerCallRunnable(lambda llm: inner, lambda http: MagicMock(), lambda: http_client)

    with pytest.raises(RuntimeError, match="boom"):
        await runnable.ainvoke({"text": "a"})

    http_client.aclose.assert_awaited_once()


def test_calls_succeed_across_event_loops_only_with_a_per_call_http_client():
    class LoopBoundHttpClient:
        """Like a pooled httpx client: usable only in the loop where it was first used."""

        def __init__(self):
            self.loop = None

        async def request(self):
            running = asyncio.get_running_loop()
            if self.loop is None:
                self.loop = running
            elif self.loop is not running:
                raise RuntimeError("Event loop is closed")
            return "ok"

        async def aclose(self):
            pass

    def build_for(http_client):
        inner = MagicMock()

        async def ainvoke(_input):
            return await http_client.request()

        inner.ainvoke = ainvoke
        return inner

    shared = LoopBoundHttpClient()
    shared_cache = PerCallRunnable(lambda llm: llm, lambda http: build_for(http), lambda: shared)
    assert asyncio.run(shared_cache.ainvoke({})) == "ok"
    with pytest.raises(RuntimeError, match="Event loop is closed"):
        asyncio.run(shared_cache.ainvoke({}))

    per_call = PerCallRunnable(lambda llm: llm, lambda http: build_for(http), LoopBoundHttpClient)
    assert asyncio.run(per_call.ainvoke({})) == "ok"
    assert asyncio.run(per_call.ainvoke({})) == "ok"
