from typing import List, Optional
from openai import OpenAI
import time

from api.schemas.params import ParamsSummarize
from api.utils.logger import logger_abrege as logger_app

SYSTEM_PROMPT = "Vous êtes un expert en résumé. Résumez le texte ci-dessous en conservant son sens principal et la langue du texte."


CONTEXT_LENGTH = 128_000  # For qwen


def summarize_text(
    text: str, model: str, client: OpenAI, params: Optional[ParamsSummarize] = None
) -> str:
    """
    Résume un texte donné en utilisant l'API OpenAI.
    """
    prompt = SYSTEM_PROMPT
    if params:
        if params.size:
            prompt += f"\n le résumé doit faire moins de {params.size}"

        if params.language:
            prompt += f"\n le résumé doit être en {params.language}"

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "developer",
                "content": prompt,
            },
            {
                "role": "user",
                "content": f"Texte : {text}",
            },
        ],
    )

    return completion.choices[0].message.content


def merge_summaries(
    summaries: List[str],
    model: str,
    client: OpenAI,
    params: Optional[ParamsSummarize] = None,
) -> str:
    """
    Combine récursivement les résumés en un seul.
    """
    nb_call = 0
    while len(summaries) > 1:
        new_summaries = []
        for i in range(0, len(summaries), 2):
            if i + 1 < len(summaries):
                combined_text = (
                    f"Résumé 1 : {summaries[i]}\nRésumé 2 : {summaries[i+1]}"
                )
                new_summary = summarize_text(
                    combined_text, model, client, params=params
                )
                new_summaries.append(new_summary)
                nb_call += 1
            else:
                new_summaries.append(summaries[i])
        summaries = new_summaries
    return summaries[0], nb_call


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
                chunk = []

    if chunk:
        all_chunks.append(f"Page{i + 1}:" + " ".join(chunk))

    return all_chunks


def process_documents(
    docs: List[str],
    model: str,
    client: OpenAI,
    params: Optional[ParamsSummarize] = None,
) -> str:
    """
    Traite une liste de documents pour produire un résumé final.
    """
    t = time.time()
    partial_summaries = []

    docs = split_texts_by_word_limit(docs, max_words=CONTEXT_LENGTH)
    nb_words = 0
    for doc in docs:
        nb_curr_words = len(doc.split())
        nb_words += nb_curr_words
        logger_app.debug(f"Current words: {nb_curr_words} - {nb_words}")
        partial_summary = summarize_text(doc, model, client, params=params)
        partial_summaries.append(partial_summary)
    logger_app.debug(f"Total words {nb_words}")
    logger_app.debug(f"Partial summaries: {len(partial_summaries)} - {time.time() - t}")
    nb_call_llm = len(partial_summaries)
    final_summary, nb_call_llm_merge = merge_summaries(
        partial_summaries, model, client, params=params
    )
    return {"summary": final_summary, "nb_call": nb_call_llm + nb_call_llm_merge}
