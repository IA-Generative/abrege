from typing import List, Optional
from openai import OpenAI
from schemas.params import ParamsSummarize


def summarize_text(
    text: str, model: str, client: OpenAI, params: Optional[ParamsSummarize] = None
) -> str:
    """
    Résume un texte donné en utilisant l'API OpenAI.
    """
    prompt = "Vous êtes un expert en résumé. Résumez le texte ci-dessous en conservant son sens principal et la langue du texte."
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


def process_documents(
    docs: List[str],
    model: str,
    client: OpenAI,
    params: Optional[ParamsSummarize] = None,
) -> str:
    """
    Traite une liste de documents pour produire un résumé final.
    """
    partial_summaries = [
        summarize_text(doc, model, client, params=params) for doc in docs
    ]
    nb_call_llm = len(partial_summaries)
    final_summary, nb_call_llm_merge = merge_summaries(
        partial_summaries, model, client, params=params
    )
    return {"summary": final_summary, "nb_call": nb_call_llm + nb_call_llm_merge}
