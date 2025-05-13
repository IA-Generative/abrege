import os
import shutil
from tiktoken import Encoding
from abrege_service.utils.tokenizer import get_tokenizer_model
import pytest


def test_get_gpt_token():
    actual = get_tokenizer_model(model_name="gpt-4")
    assert isinstance(actual, Encoding)
    full_text = "I am angry"
    tokens = actual.encode(full_text)
    assert len(tokens) > 1


def test_get_other_tokenizer():
    actual = get_tokenizer_model(model_name="bert-base-uncased", cache_dir="tokenizer/")
    assert os.path.exists("tokenizer/")
    shutil.rmtree("tokenizer/", ignore_errors=True)
    full_text = "I am angry"
    tokens = actual.encode(full_text)
    assert len(tokens) > 1


@pytest.mark.skipif(os.environ.get("HF_TOKEN") is None, reason="requires HF_TOKEN to be sure we have access to the hf repo")
def test_get_mistral_small_3_1_24B():
    model_name = "mistralai/Mistral-Small-3.1-24B-Instruct-2503"
    actual = get_tokenizer_model(model_name=model_name, cache_dir="tokenizer/")
    assert actual is not None
