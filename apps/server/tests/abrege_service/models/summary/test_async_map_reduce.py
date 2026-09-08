import pytest
import os
import json
import random
import openai
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from src.clients import celery_app, redis_client
from src.schemas.task import TaskModel, TaskForm, task_table, TaskStatus
from src.schemas.result import ResultModel
from src.schemas.parameters import SummaryParameters
from abrege_service.utils.text import (
    split_texts_by_token_limit,
    split_texts_by_word_limit,
)
from src.utils.logger import logger_abrege
from abrege_service.models.summary.parallele_summary_chain import (
    LangChainAsyncMapReduceService,
    StuffSummarizeChain,
    SummaryOutput,
    MAP_PROMPT,
)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE_URL")
OPENAI_API_MODEL = os.environ.get("OPENAI_API_MODEL")


def _check_openai_model_access() -> bool:
    if not (OPENAI_API_KEY and OPENAI_API_BASE and OPENAI_API_MODEL):
        return False
    try:
        openai.OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE).chat.completions.create(
            model=OPENAI_API_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
        )
        return True
    except Exception as e:
        logger_abrege.warning(f"OpenAI model '{OPENAI_API_MODEL}' not available for tests: {e}")
        return False


is_openai_is_set = _check_openai_model_access()


@pytest.fixture(scope="module")
def mock_llm() -> ChatOpenAI:
    model_name = os.environ.get("OPENAI_API_MODEL")
    logger_abrege.info(f"For the test we will use {model_name}")
    logger_abrege.debug(79 * "*")
    return ChatOpenAI(
        model=model_name,
        temperature=0.0,
        max_tokens=8192,
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE_URL"),
    )


def _load_local_documents(n: int = 5) -> list[str]:
    text = Path("tests/data/2106.11520v2-markitdown.md").read_text(encoding="utf-8")
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 200]
    rng = random.Random(42)
    rng.shuffle(paragraphs)
    return [paragraphs[i % len(paragraphs)] for i in range(n)]


def dummy_task_large() -> TaskModel:
    text_found = _load_local_documents(20)

    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            percentage=0.5,
            parameters=SummaryParameters(size=4000, custom_prompt="Ecris le au style de Victor Hugo"),
            output=ResultModel(
                type="ocr",
                created_at=0,
                model_name="mock",
                model_version="mock",
                updated_at=0,
                texts_found=text_found,
                percentage=0.5,
            ),
        ),
    )

    return task


@pytest.fixture(scope="module")
def dummy_task_large1() -> TaskModel:
    return dummy_task_large()


@pytest.fixture(scope="module")
def dummy_task_large2() -> TaskModel:
    return dummy_task_large()


@pytest.fixture(scope="module")
def dummy_task_large3() -> TaskModel:
    return dummy_task_large()


@pytest.fixture(scope="module")
def dummy_task_large4() -> TaskModel:
    return dummy_task_large()


@pytest.mark.skipif(condition=not is_openai_is_set, reason="Openai not set")
@pytest.mark.asyncio
async def test_map_documents(mock_llm: ChatOpenAI, dummy_task_large1: TaskModel):
    service = LangChainAsyncMapReduceService(llm=mock_llm, max_token=3_000)
    result = await service.map_documents(task=dummy_task_large1, language="french")
    max_token = mock_llm.max_tokens if mock_llm.max_tokens else 10_000
    try:
        expected_text = split_texts_by_token_limit(
            texts=dummy_task_large1.output.texts_found,
            max_tokens=max_token,
            model=mock_llm.model_name,
        )
    except Exception as e:
        logger_abrege.warning(str(e))
        expected_text = split_texts_by_word_limit(texts=dummy_task_large1.output.texts_found, max_words=int(max_token * 0.75))
    assert len(result) == len(expected_text)
    updated_task = task_table.get_task_by_id(task_id=dummy_task_large1.id)
    assert updated_task.percentage == 0.75


# TODO: need to refactor here the name of function
@pytest.mark.skipif(condition=not is_openai_is_set, reason="Openai not set")
@pytest.mark.asyncio
async def test_collapse_summary_chain(mock_llm: ChatOpenAI, dummy_task_large2: TaskModel):
    max_token = 10000
    try:
        expected_text = split_texts_by_token_limit(
            texts=dummy_task_large2.output.texts_found,
            max_tokens=max_token,
            model=mock_llm.model_name,
        )
    except Exception as e:
        logger_abrege.warning(str(e))
        expected_text = split_texts_by_word_limit(texts=dummy_task_large2.output.texts_found, max_words=int(max_token * 0.75))

    docs = [Document(page_content=text) for text in expected_text]
    service = LangChainAsyncMapReduceService(llm=mock_llm, max_token=100)
    result = await service.collapse_summary_chain(task=dummy_task_large2, docs=docs, language="french")

    assert len(result) <= len(expected_text)
    updated_task = task_table.get_task_by_id(task_id=dummy_task_large2.id)
    assert updated_task.percentage < 1


@pytest.mark.skipif(
    not os.environ.get("TOKENIZER_MODEL_NAME") or not is_openai_is_set,
    reason="No TOKENIZER_MODEL_NAME are defined",
)
@pytest.mark.asyncio
async def test_async_existing_token_summary(mock_llm: ChatOpenAI, dummy_task_large3: TaskModel):
    service = LangChainAsyncMapReduceService(llm=mock_llm, max_token=10_000)
    result = await service.map_documents(task=dummy_task_large3, language="french")
    max_token = mock_llm.max_tokens if mock_llm.max_tokens else 10_000
    expected_text = split_texts_by_token_limit(
        texts=dummy_task_large3.output.texts_found,
        max_tokens=max_token,
        model=os.environ.get("TOKENIZER_MODEL_NAME"),
    )
    assert len(result) == len(expected_text)
    updated_task = task_table.get_task_by_id(task_id=dummy_task_large3.id)
    assert updated_task.percentage < 1


@pytest.mark.skipif(condition=not is_openai_is_set, reason="Openai not set")
def test_summary(mock_llm: ChatOpenAI, dummy_task_large4: TaskModel):
    service = LangChainAsyncMapReduceService(llm=mock_llm)
    logger_abrege.debug(f"Model name {mock_llm.model_name}")
    logger_abrege.debug(79 * "*")
    task = service.process_task(dummy_task_large4)
    assert task.status == TaskStatus.COMPLETED.value
    assert task.output.summary
    assert task.output.word_count > 0 and task.output.word_count < 4000
    assert task.percentage == 1
    logger_abrege.debug(f"{mock_llm.model_name}")


# ---------------------------------------------------------------------------
# Unit tests — no LLM required (runnable is mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stuff_chain_ainvoke_returns_structured_output_keys():
    """StuffSummarizeChain.ainvoke must always return output_text and output keys."""
    fake_output = SummaryOutput(summary="Un résumé de test.")

    mock_llm = MagicMock()
    chain = StuffSummarizeChain(llm=mock_llm, prompt=MAP_PROMPT)
    runnable_mock = MagicMock()
    runnable_mock.ainvoke = AsyncMock(return_value=fake_output)
    chain._runnable = runnable_mock

    docs = [Document(page_content="Texte du document.")]
    result = await chain.ainvoke({"input_documents": docs, "language": "French"})

    assert result["output_text"] == "Un résumé de test."
    assert isinstance(result["output"], SummaryOutput)


# ---------------------------------------------------------------------------
# Unit tests — Q&A/entities/relationships extraction dispatch (no LLM required)
# ---------------------------------------------------------------------------


def test_split_task_texts_uses_token_split_by_default(monkeypatch: pytest.MonkeyPatch):
    task = dummy_task_large()
    monkeypatch.setattr(
        "abrege_service.models.summary.parallele_summary_chain.split_texts_by_token_limit",
        lambda texts, max_tokens, model: [f"token-chunk::{len(texts)}::{max_tokens}"],
    )
    service = LangChainAsyncMapReduceService(llm=MagicMock(model_name="gpt-4", max_tokens=None), max_token=3_000)

    chunks = service.split_task_texts(task)

    assert chunks == [f"token-chunk::{len(task.output.texts_found)}::3000"]


def test_split_task_texts_falls_back_to_word_split_on_error(monkeypatch: pytest.MonkeyPatch):
    task = dummy_task_large()

    def raise_error(texts, max_tokens, model):
        raise RuntimeError("tokenizer unavailable")

    monkeypatch.setattr("abrege_service.models.summary.parallele_summary_chain.split_texts_by_token_limit", raise_error)
    monkeypatch.setattr(
        "abrege_service.models.summary.parallele_summary_chain.split_texts_by_word_limit",
        lambda texts, max_words: [f"word-chunk::{len(texts)}::{max_words}"],
    )
    service = LangChainAsyncMapReduceService(llm=MagicMock(model_name="gpt-4", max_tokens=None), max_token=1_000)

    chunks = service.split_task_texts(task)

    assert chunks == [f"word-chunk::{len(task.output.texts_found)}::750"]


def test_dispatch_chunk_extraction_sends_one_celery_task(monkeypatch: pytest.MonkeyPatch):
    sent = []
    monkeypatch.setattr(celery_app, "send_task", lambda name, args, task_id=None: sent.append((name, args, task_id)))

    service = LangChainAsyncMapReduceService(llm=MagicMock(), max_token=3_000)
    service.dispatch_chunk_extraction(task_id="task-abc", chunk_index=2, text="Page3: hello world", language="French", qa_per_chunk=3)

    assert len(sent) == 1
    name, args, task_id = sent[0]
    assert name == "worker.tasks.extract_chunk_details"
    assert task_id == "task-abc:chunk:2"
    payload = json.loads(args[0])
    assert payload["task_id"] == "task-abc"
    assert payload["chunk_index"] == 2
    assert payload["page"] == 3
    assert payload["text"] == "Page3: hello world"
    assert payload["language"] == "French"
    assert payload["qa_per_chunk"] == 3


def test_dispatch_all_chunks_sets_redis_counter_and_dispatches_each_chunk(monkeypatch: pytest.MonkeyPatch):
    sent = []
    redis_calls = {}
    monkeypatch.setattr(celery_app, "send_task", lambda name, args, task_id=None: sent.append(task_id))
    monkeypatch.setattr(redis_client, "set", lambda key, value: redis_calls.__setitem__(key, value))

    service = LangChainAsyncMapReduceService(llm=MagicMock(), max_token=3_000)
    texts = ["chunk one", "chunk two", "chunk three"]
    service.dispatch_all_chunks(task_id="task-xyz", texts=texts, language="French", qa_per_chunk=3)

    assert redis_calls == {"chunk_pending:task-xyz": 3}
    assert sent == ["task-xyz:chunk:0", "task-xyz:chunk:1", "task-xyz:chunk:2"]
