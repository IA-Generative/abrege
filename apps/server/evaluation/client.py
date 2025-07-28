import os
from datasets import load_dataset
from evaluate import load
import openai

# Chargement en streaming du sous-ensemble français
dataset_stream = load_dataset(
    "csebuetnlp/xlsum",
    "french",
    cache_dir="tests/data/text",
    streaming=True,
)
dataset = dataset_stream["train"].shuffle(seed=42).take(50)
rouge_metric = load("rouge")

client = openai.OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_API_BASE"],
)
models_availables = [model.id for model in client.models.list()]
model_name = os.environ["OPENAI_API_MODEL"]
if model_name not in models_availables:
    raise ValueError(f"Model {os.environ['OPENAI_API_MODEL']} not available. Available models: {models_availables}")
