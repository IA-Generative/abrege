import pytest
import os
import random
import openai
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
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
    EntityOutput,
    RelationshipOutput,
    MAP_PROMPT,
)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE")
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
        base_url=os.environ.get("OPENAI_API_BASE"),
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
    fake_output = SummaryOutput(
        summary="Un résumé de test.",
        entities=[
            EntityOutput(
                type="PERSON",
                text="Jean Dupont",
                contexts=["Jean Dupont signe le contrat"],
                pages=[1],
            ),
            EntityOutput(
                type="DATE",
                text="2024-01-12",
                contexts=["Le 12 janvier 2024"],
                pages=[2],
            ),
        ],
    )

    mock_llm = MagicMock()
    chain = StuffSummarizeChain(llm=mock_llm, prompt=MAP_PROMPT)
    runnable_mock = MagicMock()
    runnable_mock.ainvoke = AsyncMock(return_value=fake_output)
    chain._runnable = runnable_mock

    docs = [Document(page_content="Texte du document.")]
    result = await chain.ainvoke({"input_documents": docs, "language": "French"})

    assert result["output_text"] == "Un résumé de test."
    assert isinstance(result["output"], SummaryOutput)
    assert len(result["output"].entities) == 2


@pytest.mark.asyncio
async def test_stuff_chain_entities_types_are_valid():
    """All entity types returned must belong to the EntityType literal."""
    valid_types = {
        "PERSON",
        "DATE",
        "ORGANIZATION",
        "LOCATION",
        "AMOUNT",
        "EVENT",
        "OTHER",
    }
    fake_output = SummaryOutput(
        summary="Résumé.",
        entities=[
            EntityOutput(type="PERSON", text="Marie Curie", contexts=["Prix Nobel"], pages=[3]),
            EntityOutput(
                type="ORGANIZATION",
                text="Académie des Sciences",
                contexts=["membre de"],
                pages=[3],
            ),
            EntityOutput(type="DATE", text="1903-12-10", contexts=["remise du prix"], pages=[4]),
        ],
    )

    mock_llm = MagicMock()
    chain = StuffSummarizeChain(llm=mock_llm, prompt=MAP_PROMPT)
    runnable_mock = MagicMock()
    runnable_mock.ainvoke = AsyncMock(return_value=fake_output)
    chain._runnable = runnable_mock

    docs = [Document(page_content="Marie Curie reçut le prix Nobel en 1903.")]
    result = await chain.ainvoke({"input_documents": docs, "language": "French"})

    for entity in result["output"].entities:
        assert entity.type in valid_types


@pytest.mark.asyncio
async def test_stuff_chain_entity_contexts_preserved():
    """Each entity must preserve all its context strings."""
    fake_output = SummaryOutput(
        summary="Résumé.",
        entities=[
            EntityOutput(
                type="PERSON",
                text="Jean Dupont",
                contexts=["signe le contrat", "rencontre le PDG"],
                pages=[1, 5],
            ),
        ],
    )

    mock_llm = MagicMock()
    chain = StuffSummarizeChain(llm=mock_llm, prompt=MAP_PROMPT)
    runnable_mock = MagicMock()
    runnable_mock.ainvoke = AsyncMock(return_value=fake_output)
    chain._runnable = runnable_mock

    docs = [Document(page_content="Jean Dupont signe le contrat. Jean Dupont rencontre le PDG.")]
    result = await chain.ainvoke({"input_documents": docs, "language": "French"})

    entity = result["output"].entities[0]
    assert len(entity.contexts) == 2
    assert len(entity.pages) == 2


# ---------------------------------------------------------------------------
# Integration tests — require a real LLM (OPENAI_API_KEY etc.)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def dummy_task_entities() -> TaskModel:
    return dummy_task_large()


@pytest.mark.skipif(condition=not is_openai_is_set, reason="Openai not set")
@pytest.mark.asyncio
async def test_acall_returns_entities(mock_llm: ChatOpenAI, dummy_task_entities: TaskModel):
    """acall must return a SummaryOutput with at least one entity."""
    service = LangChainAsyncMapReduceService(llm=mock_llm, max_token=10_000)
    result = await service.acall(task=dummy_task_entities)

    assert "output" in result
    assert isinstance(result["output"], SummaryOutput)
    assert isinstance(result["output"].entities, list)
    assert len(result["output"].entities) > 0, "Expected at least one extracted entity"


@pytest.mark.skipif(condition=not is_openai_is_set, reason="Openai not set")
@pytest.mark.asyncio
async def test_acall_entity_structure(mock_llm: ChatOpenAI, dummy_task_entities: TaskModel):
    """Every entity in the final output must have a non-empty type and text."""
    service = LangChainAsyncMapReduceService(llm=mock_llm, max_token=10_000)
    result = await service.acall(task=dummy_task_entities)

    for entity in result["output"].entities:
        assert entity.type, "Entity type must not be empty"
        assert entity.text, "Entity text must not be empty"
        assert isinstance(entity.contexts, list)
        assert isinstance(entity.pages, list)


@pytest.mark.asyncio
async def test_stuff_chain_relationships_reference_valid_entity_indices():
    """Relationship indices must point to existing entities in the list."""
    entities = [
        EntityOutput(
            type="PERSON",
            text="Jean Dupont",
            contexts=["signe le contrat avec Acme"],
            pages=[1],
        ),
        EntityOutput(
            type="ORGANIZATION",
            text="Acme",
            contexts=["Jean Dupont signe le contrat avec Acme"],
            pages=[1],
        ),
        EntityOutput(
            type="DATE",
            text="2024-01-12",
            contexts=["contrat signé le 12 janvier 2024"],
            pages=[1],
        ),
    ]
    fake_output = SummaryOutput(
        summary="Jean Dupont a signé un contrat avec Acme le 12 janvier 2024.",
        entities=entities,
        relationships=[
            RelationshipOutput(
                source_index=0,
                target_index=1,
                relationship_type="SIGNED_CONTRACT_WITH",
                description="Jean Dupont a signé un contrat avec Acme.",
            ),
            RelationshipOutput(
                source_index=0,
                target_index=2,
                relationship_type="ACTED_ON_DATE",
                description="Jean Dupont a signé le contrat le 12 janvier 2024.",
            ),
        ],
    )

    mock_llm = MagicMock()
    chain = StuffSummarizeChain(llm=mock_llm, prompt=MAP_PROMPT)
    runnable_mock = MagicMock()
    runnable_mock.ainvoke = AsyncMock(return_value=fake_output)
    chain._runnable = runnable_mock

    docs = [Document(page_content="Jean Dupont a signé un contrat avec Acme le 12 janvier 2024.")]
    result = await chain.ainvoke({"input_documents": docs, "language": "French"})

    output: SummaryOutput = result["output"]
    nb_entities = len(output.entities)
    for rel in output.relationships:
        assert 0 <= rel.source_index < nb_entities, f"source_index={rel.source_index} out of range"
        assert 0 <= rel.target_index < nb_entities, f"target_index={rel.target_index} out of range"
        assert rel.source_index != rel.target_index, "A relationship must link two different entities"
        assert rel.relationship_type, "relationship_type must not be empty"
        assert rel.description, "description must not be empty"


@pytest.mark.skipif(condition=not is_openai_is_set, reason="Openai not set")
@pytest.mark.asyncio
async def test_acall_returns_relationships(mock_llm: ChatOpenAI, dummy_task_entities: TaskModel):
    """acall must return a SummaryOutput with relationships whose indices are valid."""
    service = LangChainAsyncMapReduceService(llm=mock_llm, max_token=10_000)
    result = await service.acall(task=dummy_task_entities)

    output: SummaryOutput = result["output"]
    nb_entities = len(output.entities)
    for rel in output.relationships:
        assert 0 <= rel.source_index < nb_entities
        assert 0 <= rel.target_index < nb_entities
        assert rel.source_index != rel.target_index
