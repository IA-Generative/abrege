from abrege_service.utils.text import (
    split_texts_by_word_limit,
    split_texts_by_token_limit,
)
import tiktoken


def test_splite_texts_by_word_limit():
    texts = [
        "This is a test text that is quite long and should be split into smaller chunks.",
        "Another test text that also needs to be split.",
    ]  # 25 words --> 3 split
    max_words = 10
    result = split_texts_by_word_limit(texts, max_words)
    assert len(result) == 3
    assert result[0] == "Page1: This is a test text that is quite long"
    assert result[1] == "Page1: and should be split into smaller chunks. Page2: Another"
    assert result[2] == "Page2: test text that also needs to be split."


def test_no_segment_exceeds_token_limit():
    encoding = tiktoken.encoding_for_model("gpt-4")
    texts = [
        "Ceci est un texte court.",
        "Ceci est un texte beaucoup plus long qui contient plusieurs mots et qui devrait être divisé correctement en segments selon la limite de tokens spécifiée.",
    ]
    max_tokens = 20
    segments = split_texts_by_token_limit(texts, max_tokens, model="gpt-4")
    for segment in segments:
        token_count = len(encoding.encode(segment))
        assert token_count <= max_tokens, "Segment exceeds {max_tokens} tokens."


def test_reconstructed_content_includes_original():
    texts = [
        "Ceci est un texte court.",
        "Ceci est un texte beaucoup plus long qui contient plusieurs mots et qui devrait être divisé correctement en segments selon la limite de tokens spécifiée.",
    ]
    max_tokens = 20
    segments = split_texts_by_token_limit(texts, max_tokens, model="gpt-4")
    joined = " ".join(segments)
    for i, text in enumerate(texts):
        prefix = f"Page{i + 1}:"
        assert prefix in joined
        for word in text.split():
            assert word in joined


def test_reconstructed_content_long_text_original():
    texts = [
        " ".join([str(i) for i in range(100)]),
        " ".join([str(i) for i in range(100)]),
    ]
    max_tokens = 50
    segments = split_texts_by_token_limit(texts, max_tokens, model="gpt-4")
    joined = " ".join(segments)
    for i, text in enumerate(texts):
        prefix = f"Page{i + 1}: "
        assert prefix in joined
        for word in text.split():
            assert word in joined
