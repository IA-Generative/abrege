import os
from datasets import load_dataset
from evaluate import load
import openai
from langchain_openai import ChatOpenAI

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

llm_judge = ChatOpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    openai_api_base=os.environ["OPENAI_API_BASE"],
    temperature=0,
    model="gemma2-27b",
)

models_availables = [model.id for model in client.models.list()]
model_name = os.environ["OPENAI_API_MODEL"]
if model_name not in models_availables:
    raise ValueError(f"Model {os.environ['OPENAI_API_MODEL']} not available. Available models: {models_availables}")
