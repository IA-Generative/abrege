import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.repositories.chunk_repo import ChunkRepository, _l2_norm, _cosine_similarity
from src.models.chunk import ChunkBase, ChunkModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk_base(**overrides) -> ChunkBase:
    defaults = dict(
        storage_path="s3://bucket/file.pdf",
        content_hash="abc123",
        text="hello world",
        user_id="user-1",
        group_id=None,
        model_name="text-embedding-ada-002",
        vector=[1.0, 0.0, 0.0],
        vector_size=3,
        extras=None,
    )
    defaults.update(overrides)
    return ChunkBase(**defaults)  # ty:ignore[invalid-argument-type]


def _make_chunk_model(**overrides) -> ChunkModel:
    defaults = dict(
        id="chunk-id-1",
        created_at=1700000000,
        storage_path="s3://bucket/file.pdf",
        content_hash="abc123",
        text="hello world",
        user_id="user-1",
        group_id=None,
        model_name="text-embedding-ada-002",
        vector=[1.0, 0.0, 0.0],
        vector_size=3,
        extras=None,
    )
    defaults.update(overrides)
    return ChunkModel(**defaults)  # ty:ignore[invalid-argument-type]


def _mock_row(chunk_model: ChunkModel) -> MagicMock:
    """Create a mock SQLAlchemy row that supports attribute access."""
    row = MagicMock()
    for field in chunk_model.model_fields:
        setattr(row, field, getattr(chunk_model, field))
    return row


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def repo():
    return ChunkRepository()


# ---------------------------------------------------------------------------
# Tests: insert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_insert(db, repo):
    chunk_base = _make_chunk_base()
    expected_model = _make_chunk_model()

    # mock_row = _mock_row(expected_model)
    db.refresh = AsyncMock(side_effect=lambda r: None)

    with (
        patch("src.repositories.chunk_repo.uuid.uuid4", return_value="chunk-id-1"),
        patch("src.repositories.chunk_repo.time.time", return_value=1700000000),
        patch.object(ChunkModel, "model_validate", return_value=expected_model),
    ):
        result = await repo.insert(db, chunk_base)

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()
    assert result.id == "chunk-id-1"
    assert result.storage_path == chunk_base.storage_path
    assert result.content_hash == chunk_base.content_hash


# ---------------------------------------------------------------------------
# Tests: upsert_bulk
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_bulk_empty_list(db, repo):
    result = await repo.upsert_bulk(db, [])
    assert result == []


@pytest.mark.asyncio
async def test_upsert_bulk_single_chunk(db, repo):
    chunk_base = _make_chunk_base()
    expected_model = _make_chunk_model()

    with (
        patch.object(repo, "delete_by_content_hash", new_callable=AsyncMock) as mock_delete,
        patch("src.repositories.chunk_repo.uuid.uuid4", return_value="chunk-id-1"),
        patch("src.repositories.chunk_repo.time.time", return_value=1700000000),
        patch.object(ChunkModel, "model_validate", return_value=expected_model),
    ):
        result = await repo.upsert_bulk(db, [chunk_base])

    mock_delete.assert_awaited_once_with(db, "abc123", "user-1")
    db.add.assert_called_once()
    assert len(result) == 1
    assert result[0].id == "chunk-id-1"


@pytest.mark.asyncio
async def test_upsert_bulk_multiple_chunks(db, repo):
    chunks = [
        _make_chunk_base(content_hash="hash-a", text="first"),
        _make_chunk_base(content_hash="hash-b", text="second"),
    ]
    models = [
        _make_chunk_model(id="id-a", content_hash="hash-a", text="first"),
        _make_chunk_model(id="id-b", content_hash="hash-b", text="second"),
    ]

    call_count = 0

    def validate_side_effect(_row):
        nonlocal call_count
        result = models[call_count]
        call_count += 1
        return result

    with (
        patch.object(repo, "delete_by_content_hash", new_callable=AsyncMock),
        patch("src.repositories.chunk_repo.uuid.uuid4", side_effect=["id-a", "id-b"]),
        patch("src.repositories.chunk_repo.time.time", return_value=1700000000),
        patch.object(ChunkModel, "model_validate", side_effect=validate_side_effect),
    ):
        result = await repo.upsert_bulk(db, chunks)

    assert len(result) == 2
    assert result[0].content_hash == "hash-a"
    assert result[1].content_hash == "hash-b"


# ---------------------------------------------------------------------------
# Tests: delete_by_content_hash
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_by_content_hash(db, repo):
    await repo.delete_by_content_hash(db, "abc123", "user-1")

    db.execute.assert_awaited_once()
    db.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Tests: get_by_content_hash
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_content_hash_returns_results(db, repo):
    expected = _make_chunk_model()
    mock_row = _mock_row(expected)

    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [mock_row]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    db.execute = AsyncMock(return_value=result_mock)

    with patch.object(ChunkModel, "model_validate", return_value=expected):
        result = await repo.get_by_content_hash(db, "abc123", "user-1")

    assert len(result) == 1
    assert result[0].id == "chunk-id-1"


@pytest.mark.asyncio
async def test_get_by_content_hash_empty(db, repo):
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    db.execute = AsyncMock(return_value=result_mock)

    result = await repo.get_by_content_hash(db, "nonexistent", "user-1")

    assert result == []


# ---------------------------------------------------------------------------
# Tests: get_by_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_user(db, repo):
    expected = _make_chunk_model()
    mock_row = _mock_row(expected)

    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [mock_row]
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    db.execute = AsyncMock(return_value=result_mock)

    with patch.object(ChunkModel, "model_validate", return_value=expected):
        result = await repo.get_by_user(db, "user-1")

    assert len(result) == 1
    assert result[0].user_id == "user-1"


# ---------------------------------------------------------------------------
# Tests: search
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_returns_sorted_results(db, repo):
    chunks = [
        _make_chunk_model(id="c1", vector=[1.0, 0.0, 0.0], text="exact match"),
        _make_chunk_model(id="c2", vector=[0.5, 0.5, 0.0], text="partial match"),
        _make_chunk_model(id="c3", vector=[0.0, 1.0, 0.0], text="orthogonal"),
    ]

    with patch.object(repo, "get_by_content_hash", new_callable=AsyncMock, return_value=chunks):
        results = await repo.search(
            db,
            user_id="user-1",
            query_vector=[1.0, 0.0, 0.0],
            top_k=3,
            content_hash="abc123",
        )

    assert len(results) == 3
    assert results[0].id == "c1"
    assert results[0].score == 1.0
    assert results[1].id == "c2"
    assert results[2].id == "c3"
    assert results[0].score >= results[1].score >= results[2].score


@pytest.mark.asyncio
async def test_search_top_k_limits_results(db, repo):
    chunks = [_make_chunk_model(id=f"c{i}", vector=[float(i), 0.0, 0.0]) for i in range(1, 6)]

    with patch.object(repo, "get_by_content_hash", new_callable=AsyncMock, return_value=chunks):
        results = await repo.search(
            db,
            user_id="user-1",
            query_vector=[1.0, 0.0, 0.0],
            top_k=2,
            content_hash="abc123",
        )

    assert len(results) == 2


@pytest.mark.asyncio
async def test_search_threshold_filters_results(db, repo):
    chunks = [
        _make_chunk_model(id="c1", vector=[1.0, 0.0, 0.0]),
        _make_chunk_model(id="c2", vector=[0.0, 1.0, 0.0]),
    ]

    with patch.object(repo, "get_by_content_hash", new_callable=AsyncMock, return_value=chunks):
        results = await repo.search(
            db,
            user_id="user-1",
            query_vector=[1.0, 0.0, 0.0],
            top_k=10,
            content_hash="abc123",
            threshold=0.5,
        )

    assert len(results) == 1
    assert results[0].id == "c1"


@pytest.mark.asyncio
async def test_search_empty_chunks(db, repo):
    with patch.object(repo, "get_by_content_hash", new_callable=AsyncMock, return_value=[]):
        results = await repo.search(db, user_id="user-1", query_vector=[1.0, 0.0, 0.0], content_hash="abc123")

    assert results == []


@pytest.mark.asyncio
async def test_search_without_content_hash_uses_get_by_user(db, repo):
    chunks = [_make_chunk_model(id="c1", vector=[1.0, 0.0, 0.0])]

    with patch.object(repo, "get_by_user", new_callable=AsyncMock, return_value=chunks) as mock_get:
        results = await repo.search(db, user_id="user-1", query_vector=[1.0, 0.0, 0.0], content_hash=None)

    mock_get.assert_awaited_once_with(db, "user-1")
    assert len(results) == 1


@pytest.mark.asyncio
async def test_search_skips_mismatched_vector_dimensions(db, repo):
    chunks = [
        _make_chunk_model(id="c1", vector=[1.0, 0.0, 0.0]),
        _make_chunk_model(id="c2", vector=[1.0, 0.0]),  # wrong dim
    ]

    with patch.object(repo, "get_by_content_hash", new_callable=AsyncMock, return_value=chunks):
        results = await repo.search(db, user_id="user-1", query_vector=[1.0, 0.0, 0.0], content_hash="abc123")

    assert len(results) == 1
    assert results[0].id == "c1"


# ---------------------------------------------------------------------------
# Tests: helper functions
# ---------------------------------------------------------------------------


def test_l2_norm():
    assert _l2_norm([3.0, 4.0]) == 5.0
    assert _l2_norm([1.0, 0.0, 0.0]) == 1.0


def test_l2_norm_zero_vector():
    assert _l2_norm([0.0, 0.0, 0.0]) == 1.0


def test_cosine_similarity_identical():
    v = [1.0, 0.0, 0.0]
    assert _cosine_similarity(v, v, _l2_norm(v)) == 1.0


def test_cosine_similarity_orthogonal():
    a = [1.0, 0.0, 0.0]
    b = [0.0, 1.0, 0.0]
    assert _cosine_similarity(a, b, _l2_norm(a)) == 0.0


def test_cosine_similarity_opposite():
    a = [1.0, 0.0]
    b = [-1.0, 0.0]
    assert _cosine_similarity(a, b, _l2_norm(a)) == -1.0
