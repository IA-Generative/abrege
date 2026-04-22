import openai
from abrege_service.config.openai import OpenAISettings
from loguru import logger

openai_settings = OpenAISettings()


class ChunkingModel:
    def __init__(
        self,
        embedding_model: str = openai_settings.EMBEDDING_MODEL,
        client: openai.OpenAI = openai.OpenAI(
            api_key=openai_settings.OPENAI_API_KEY,
            base_url=openai_settings.OPENAI_API_BASE,
        ),
    ):
        self.embedding_model = embedding_model
        self.client = client

    def process(self, texts: list[str]) -> list[list[float]]:
        res = self.client.embeddings.create(input=texts, model=self.embedding_model)
        logger.debug(f"Embedding {len(texts)} texts with model {self.embedding_model}: data_len={len(getattr(res, 'data', []))}")
        # The SDK returns objects in `res.data` with an `embedding` attribute
        return [item.embedding for item in res.data]


class Chunker:
    SEPARATORS = ["\n\n", "\n", ". ", " "]

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using decreasing granularity separators."""
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        # Find the best separator that appears in the text
        separator = ""
        remaining_separators = []
        for i, sep in enumerate(separators):
            if sep in text:
                separator = sep
                remaining_separators = separators[i + 1 :]
                break

        # If no separator found, hard split as last resort
        if not separator:
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                chunks.append(text[start:end])
                start += self.chunk_size - self.chunk_overlap
            return chunks

        # Split on the chosen separator
        parts = text.split(separator)

        # Merge small parts into chunks respecting chunk_size
        chunks: list[str] = []
        current = ""
        for part in parts:
            candidate = current + separator + part if current else part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # If a single part exceeds chunk_size, split it further
                if len(part) > self.chunk_size and remaining_separators:
                    sub_chunks = self._split_text(part, remaining_separators)
                    chunks.extend(sub_chunks)
                    current = ""
                else:
                    current = part
        if current:
            chunks.append(current)

        return chunks

    def process(self, text: str) -> list[str]:
        raw_chunks = self._split_text(text, self.SEPARATORS)

        if self.chunk_overlap <= 0 or len(raw_chunks) <= 1:
            return raw_chunks

        # Rebuild chunks with overlap
        result: list[str] = []
        for i, chunk in enumerate(raw_chunks):
            if i == 0:
                result.append(chunk)
                continue
            # Take the tail of the previous chunk as overlap prefix
            prev = raw_chunks[i - 1]
            overlap = prev[-self.chunk_overlap :] if len(prev) > self.chunk_overlap else prev
            result.append(overlap + chunk)

        return result
