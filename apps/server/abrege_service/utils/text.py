from typing import List, Union
import tiktoken
from transformers import AutoTokenizer
from .tokenizer import get_tokenizer_model
from src.utils.logger import logger_abrege


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


def split_texts_by_token_limit(texts: List[str], max_tokens: int, model: str = "gpt-4", cache_dir: str = None) -> List[str]:
    encoding: Union[tiktoken.Encoding, AutoTokenizer] = get_tokenizer_model(model, cache_dir=cache_dir)
    all_chunks = []
    chunk_token_id = []
    for i, text in enumerate(texts):
        prefix = f"Page{i + 1}: "

        full_text = prefix + text
        tokens = encoding.encode(full_text)
        logger_abrege.info(prefix + f"input token size {len(tokens)}")

        for token in tokens:
            chunk_token_id.append(token)
            if len(chunk_token_id) >= max_tokens:
                chunk_text = encoding.decode(chunk_token_id)
                logger_abrege.info(f"output {len(chunk_token_id)}")
                all_chunks.append(chunk_text)
                chunk_token_id = encoding.encode(" " + prefix)

    if chunk_token_id != [encoding.encode(prefix)]:
        chunk_text = encoding.decode(chunk_token_id)
        all_chunks.append(chunk_text)
        logger_abrege.info(f"output {len(chunk_token_id)} ")

    return all_chunks


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
