from typing import List, Optional
from openai import OpenAI
import time

from api.utils.logger import logger_abrege as logger_app
from abrege_service.utils.text import split_texts_by_word_limit
from abrege_service.prompts.prompting import generate_prompt


CONTEXT_LENGTH = 128_000  # For qwen


def summarize_text(model: str, client: OpenAI, prompt: str, temperature: float = 0.0) -> str:
    """
    Résume un texte donné en utilisant l'API OpenAI.
    """

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Vous êtes un expert en résumé. Résumez le texte ci-dessous en conservant son sens principal et la langue du texte.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )

    return completion.choices[0].message.content


def merge_summaries(
    summaries: List[str],
    model: str,
    client: OpenAI,
    size: Optional[int] = 300,
    language: Optional[str] = None,
) -> str:
    """
    Combine récursivement les résumés en un seul.
    """
    nb_call = 0
    while len(summaries) > 1:
        new_summaries = []
        for i in range(0, len(summaries), 2):
            if i + 1 < len(summaries):
                prompt = generate_prompt(
                    template_name="segement_summary_promt.jinja2",
                    context={
                        "size": size,
                        "language": language,
                        "summaries": [summaries[i], summaries[i + 1]],
                    },
                )
                new_summary = summarize_text(model, client, prompt)
                new_summaries.append(new_summary)
                nb_call += 1
            else:
                new_summaries.append(summaries[i])
        summaries = new_summaries
    return summaries[0], nb_call


def process_documents(
    docs: List[str],
    model: str,
    client: OpenAI,
    size: Optional[int] = 300,
    language: Optional[str] = None,
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
        prompt = generate_prompt(
            template_name="segement_summary_promt.jinja2",
            context={
                "size": size,
                "language": language,
                "summaries": [doc],
            },
        )
        partial_summary = summarize_text(model, client, prompt=prompt)
        partial_summaries.append(partial_summary)
    logger_app.debug(f"Total words {nb_words}")
    logger_app.debug(f"Partial summaries: {len(partial_summaries)} - {time.time() - t}")
    nb_call_llm = len(partial_summaries)
    final_summary, nb_call_llm_merge = merge_summaries(partial_summaries, model, client)
    return {"summary": final_summary, "nb_call": nb_call_llm + nb_call_llm_merge}
