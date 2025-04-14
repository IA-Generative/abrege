from openai import OpenAI
from api.config.openai import OpenAISettings


client = OpenAI(api_key=OpenAISettings().OPENAI_API_KEY,
                base_url=OpenAISettings().OPENAI_API_BASE)
models_available = [model.id for model in client.models.list().data]
