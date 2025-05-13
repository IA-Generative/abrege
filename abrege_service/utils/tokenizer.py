import os
from typing import Union
from transformers import AutoTokenizer
import tiktoken


def get_tokenizer_model(model_name: str, cache_dir: str = os.environ.get("HF_HOME")) -> Union[tiktoken.Encoding, AutoTokenizer]:
    if model_name.startswith("gpt-"):
        return tiktoken.encoding_for_model(model_name)
    return AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
