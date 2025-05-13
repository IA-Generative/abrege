import os
import shutil
from tiktoken import Encoding
from abrege_service.utils.tokenizer import get_tokenizer_model


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
