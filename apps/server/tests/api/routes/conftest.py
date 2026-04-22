"""Shared fixtures for API route tests.

Overrides FastAPI dependencies (DB session, auth) so tests never hit a real database.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import fastapi as _fastapi

from api.core.security.token import RequestContext
from api.core.security.factory import TokenVerifier
from src.internal.db import get_async_session_dep
from src.services.task_service import TaskService

FastAPI = _fastapi.FastAPI


# ---------------------------------------------------------------------------
# Auth override
# ---------------------------------------------------------------------------


def _fake_token_verifier():
    """Returns a dependency that always authenticates as user 'dev'."""

    def override(request=None):
        return RequestContext(user_id="dev", is_admin=False)

    return override


# ---------------------------------------------------------------------------
# DB session override
# ---------------------------------------------------------------------------


def _fake_db_session():
    """Returns an AsyncMock session so routes never touch a real DB."""
    session = AsyncMock()
    return session


# ---------------------------------------------------------------------------
# TaskService override
# ---------------------------------------------------------------------------


def _make_mock_task_service():
    svc = MagicMock(spec=TaskService)
    # Make all methods async by default
    for attr in dir(TaskService):
        if attr.startswith("_"):
            continue
        method = getattr(svc, attr, None)
        if callable(method):
            setattr(svc, attr, AsyncMock())
    return svc


@pytest.fixture
def mock_task_service():
    return _make_mock_task_service()


@pytest.fixture
def app_with_overrides(mock_task_service):
    """Creates a FastAPI app factory that overrides DB + auth + TaskService.

    Usage in tests:
        def test_x(app_with_overrides, mock_task_service):
            app = app_with_overrides(router)
            client = TestClient(app)
            mock_task_service.get_task_by_id.return_value = ...
    """

    def _factory(*routers):
        app = FastAPI()
        for r in routers:
            app.include_router(r)

        app.dependency_overrides[get_async_session_dep] = _fake_db_session
        app.dependency_overrides[TokenVerifier] = _fake_token_verifier()
        app.dependency_overrides[TaskService] = lambda: mock_task_service

        return app

    return _factory
