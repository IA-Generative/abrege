from typing import List
import tiktoken


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


def split_texts_by_token_limit(texts: List[str], max_tokens: int, model: str = "gpt-4") -> List[str]:
    encoding = tiktoken.encoding_for_model(model)
    all_chunks = []

    for i, text in enumerate(texts):
        prefix = f"Page{i + 1}: "

        full_text = prefix + text
        tokens = encoding.encode(full_text)

        if len(tokens) <= max_tokens:
            all_chunks.append(full_text)
        else:
            start = 0
            while start < len(tokens):
                end = min(start + max_tokens, len(tokens))
                chunk_tokens = tokens[start:end]
                chunk_text = encoding.decode(chunk_tokens)
                all_chunks.append(chunk_text)
                start = end

    return all_chunks
