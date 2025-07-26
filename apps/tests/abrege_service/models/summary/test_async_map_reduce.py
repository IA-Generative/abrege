import pytest
import openai
import os
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from src.schemas.task import TaskModel, TaskForm, task_table, TaskStatus
from src.schemas.result import ResultModel
from src.schemas.parameters import SummaryParameters
from datasets import load_dataset
from abrege_service.utils.text import (
    split_texts_by_token_limit,
    split_texts_by_word_limit,
)
from src.utils.logger import logger_abrege
from abrege_service.models.summary.parallele_summary_chain import (
    LangChainAsyncMapReduceService,
)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE")
is_openai_is_set = all([OPENAI_API_BASE, OPENAI_API_KEY])


@pytest.fixture(scope="module")
def mock_llm() -> ChatOpenAI:
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )
    model_name = [model.id for model in client.models.list()][0]
    logger_abrege.info(f"For the test we will use {model_name}")
    logger_abrege.debug(79 * "*")
    return ChatOpenAI(
        model=model_name,
        temperature=0.0,
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )


def dummy_task_large() -> TaskModel:
    dataset_stream = load_dataset(
        "csebuetnlp/xlsum",
        "french",
        cache_dir="tests/data/text",
        streaming=True,
    )
    dataset = dataset_stream["train"].shuffle(seed=42).take(20)
    text_found = []
    for data in dataset:
        assert "text" in data
        assert "summary" in data
        text_found.append(data["text"])

    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
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
    service = LangChainAsyncMapReduceService(llm=mock_llm, max_token=10_000)
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
    assert updated_task.percentage < 1


# TODO: need to refactor here the name of function
@pytest.mark.skipif(condition=not is_openai_is_set, reason="Openai not set")
@pytest.mark.asyncio
async def test_collapse_summary_chain(mock_llm: ChatOpenAI, dummy_task_large2: TaskModel):
    max_token = 50
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

    assert len(result) < len(expected_text)
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
