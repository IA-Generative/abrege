from unittest.mock import MagicMock

from langchain_core.runnables import Runnable

from abrege_service.models.summary.chunk_chain import CHUNK_PROMPT, ChunkingOutput, build_chunk_runnable


def test_chunk_prompt_formats_text():
    formatted = CHUNK_PROMPT.format(text="Le ciel est bleu. La finance est en hausse.")
    assert "Le ciel est bleu. La finance est en hausse." in formatted


def test_build_chunk_runnable_returns_a_runnable():
    runnable = build_chunk_runnable(MagicMock())
    assert isinstance(runnable, Runnable)


def test_chunking_output_defaults_to_empty_list():
    assert ChunkingOutput().chunks == []


def test_chunking_output_accepts_multiple_chunks():
    output = ChunkingOutput(chunks=["Premier sujet.", "Deuxième sujet."])
    assert len(output.chunks) == 2
