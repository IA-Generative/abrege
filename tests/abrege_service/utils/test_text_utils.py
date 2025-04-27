from abrege_service.utils.text import split_texts_by_word_limit


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
