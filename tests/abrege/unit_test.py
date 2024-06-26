import pytest
import numpy as np

from abrege.extractive_summary import (
    EmbeddingModel,
    build_text_prompt_kmeans,
    build_weight,
    split_sentences,
    text_rank_iterator,
)


@pytest.fixture
def small_text() -> str:
    text = "A sentence. " * 3
    text += "Another sentence. " * 3
    text += "Again another sentence. " * 3
    text += "A final sentence."
    return text


@pytest.fixture
def custom_encode():
    def encode(list_chunk):
        res = []
        for chunk in list_chunk:
            if chunk == "A sentence.":
                res.append([0.3, 0.7])
            elif chunk == "Another sentence.":
                res.append([1, 0])
            elif chunk == "Again another sentence.":
                res.append([0, 1])
            elif chunk == "A final sentence.":
                res.append([0.7, 0.3])

        return np.array(res)

    return encode


class MockEmbeddingModel(EmbeddingModel):
    def __init__(self, model, value=1.0):
        self._model = model
        self.value = value
        self.model_class = "HuggingFaceEmbeddings"

    def encode(self, list_chunk: list[str]) -> np.ndarray:
        return np.array([[self.value] for _ in range(len(list_chunk))])


class TestExtractiveSummary:

    # Init a false model for encodings that returns 0.1 for everything
    mock_embedding_model = MockEmbeddingModel(None, 1.0)

    @staticmethod
    def test_EmbeddingModel_arguments():
        with pytest.raises(ValueError):
            EmbeddingModel(None)  # "Clearly not a model"

    @staticmethod
    def test_split_sentences():
        text = "Sometimes. A small test. Is worth. A thousand lignes of code"
        list_sentences = split_sentences(text)

        assert list_sentences == [
            "Sometimes.",
            "A small test.",
            "Is worth.",
            "A thousand lignes of code",
        ]

    def test_build_weight(self):
        list_chunks = ["a", "a", "a"]

        weight = build_weight(list_chunks, self.mock_embedding_model)

        expected_weight = {(0, 1): 1, (0, 2): 1, (1, 2): 1}

        assert expected_weight == weight

    def test_text_rank_iterator2_distant_chunk(self):
        # Cannot test the page rank algorithm, so insteand, we ensure that each
        # sentences is yielded once through all the iterator and no more
        list_chunk = ["a", "b", "c"]

        # We need sentences to be far appart
        mock_embedding_model = MockEmbeddingModel(None, 0.1)
        iterator = iter(text_rank_iterator(list_chunk, mock_embedding_model))

        idx_chunk = []
        try:
            while True:
                idx_chunk.append(next(iterator))
        except StopIteration:
            pass

        set_idx = set(idx_chunk)

        assert set_idx == {0, 1, 2}
        assert len(set_idx) == len(list_chunk)

    def test_text_rank_iterator2_close_chunk(self):
        # Close chunk so only one element should be iterated
        list_chunk = ["a"] * 100
        iterator = iter(text_rank_iterator(list_chunk, self.mock_embedding_model))

        idx_chunk = []
        try:
            while True:
                idx_chunk.append(next(iterator))
        except StopIteration:
            pass

        assert len(idx_chunk) == 1

    @staticmethod
    @pytest.mark.skip(reason="No idea on how to test this")
    def test_split_chunk():
        pass

    def test_build_text_prompt_kmeans_sentences(self, small_text, custom_encode):
        # Ce qu'on peut tester : On construit un certain texte qui euh...
        # contient autant d'elements que de chunks demandés
        # On peut le faire avec 10 phrases en entrée, s'assurer qu'il en sort 5
        # c'est déjà ça

        previous_encode = self.mock_embedding_model.encode
        self.mock_embedding_model.encode = custom_encode

        # Small preassertion
        expected_split = (
            ["A sentence."] * 3
            + ["Another sentence."] * 3
            + ["Again another sentence."] * 3
            + ["A final sentence."]
        )

        assert expected_split == split_sentences(small_text)

        extractive_summary = build_text_prompt_kmeans(
            text=small_text,
            size=0,  # We don't care cause we chunk by sentences
            n_clusters=4,
            chunk_type="sentences",
            embedding_model=self.mock_embedding_model,
        )

        assert "".join(extractive_summary) == (
            "A sentence.Another sentence.Again another sentence.A final sentence."
        )

        # Clear the mock
        self.mock_embedding_model.encode = previous_encode

    @staticmethod
    @pytest.mark.skip(reason="No idea on how to test this")
    def test_build_text_prompt_kmeans_chunk():
        pass
