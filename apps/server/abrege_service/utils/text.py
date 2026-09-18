from typing import List

# Commonly-cited average for BPE tokenizers (OpenAI's own docs use it): about 0.75 words
# per token, i.e. ~4 characters per token for English/French-ish text. Used instead of an
# exact tokenizer (tiktoken/transformers) so chunking doesn't need a model-specific
# encoding as a dependency - an estimate is enough since chunk boundaries only need to
# roughly respect the model's context limit, not hit it exactly.
WORDS_PER_TOKEN = 0.75


def split_texts_by_word_limit(texts: List[str], max_words: int) -> List[str]:
    all_chunks = []
    chunk = []

    for i, text in enumerate(texts):
        text = f"Page{i + 1}: {text}"
        words = text.split()

        for word in words:
            chunk.append(word)
            if len(chunk) >= max_words:
                all_chunks.append(" ".join(chunk))
                chunk = [f"Page{i + 1}:"]

    if chunk:
        all_chunks.append(" ".join(chunk))

    return all_chunks


def split_texts_by_token_limit(texts: List[str], max_tokens: int) -> List[str]:
    max_words = max(1, int(max_tokens * WORDS_PER_TOKEN))
    return split_texts_by_word_limit(texts, max_words)


def sum_words(texts: List[str]) -> int:
    return sum(len(text.split()) for text in texts)


def group_by_max_word_sum(texts: List[str], threshold: int) -> List[List[str]]:
    groups: List[List[str]] = []
    current_group: List[str] = []
    current_sum = 0

    for text in texts:
        word_count = len(text.split())
        if current_sum + word_count <= threshold:
            current_group.append(text)
            current_sum += word_count
        else:
            if current_group:
                groups.append(current_group)
            current_group = [text]
            current_sum = word_count

    if current_group:
        groups.append(current_group)

    return groups
