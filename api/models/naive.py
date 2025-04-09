from typing import List, Optional
from openai import OpenAI
from schemas.params import ParamsSummarize
import logging
import time


def summarize_text(text: str, model: str, client: OpenAI, params: Optional[ParamsSummarize] = None) -> str:
    """
    Résume un texte donné en utilisant l'API OpenAI.
    """
    logging.info(f"Début du résumé d'un texte de {len(text)} caractères")
    start_time = time.time()
    
    prompt = "Vous êtes un expert en résumé. Résumez le texte ci-dessous en conservant son sens principal et la langue du texte."
    if params:
        if params.size:
            prompt += f"\n le résumé doit faire moins de {params.size}"
            logging.debug(f"Taille de résumé spécifiée: {params.size}")

        if params.language:
            prompt += f"\n le résumé doit être en {params.language}"
            logging.debug(f"Langue de résumé spécifiée: {params.language}")

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
    elapsed = time.time() - start_time
    logging.info(f"Résumé généré en {elapsed:.2f} secondes")
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
    logging.info(f"Début de la fusion de {len(summaries)} résumés")
    start_time = time.time()
    nb_call = 0
    while len(summaries) > 1:
        logging.debug(f"Iteration {nb_call + 1}: {len(summaries)} résumés à fusionner")
        new_summaries = []
        for i in range(0, len(summaries), 2):
            if i + 1 < len(summaries):
                logging.debug(f"Fusion des résumés {i} et {i+1}")
                combined_text = f"Résumé 1 : {summaries[i]}\nRésumé 2 : {summaries[i + 1]}"
                new_summary = summarize_text(combined_text, model, client, params=params)
                new_summaries.append(new_summary)
                nb_call += 1
            else:
                logging.debug(f"Résumé {i} conservé sans fusion")
                new_summaries.append(summaries[i])
        summaries = new_summaries
    
    elapsed = time.time() - start_time
    logging.info(f"Fusion terminée en {elapsed:.2f} secondes avec {nb_call} appels")
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
    logging.info(f"Début du traitement de {len(docs)} documents")
    start_time = time.time()
    
    partial_summaries = []
    for i, doc in enumerate(docs):
        logging.debug(f"Résumé du document {i+1}/{len(docs)}")
        summary = summarize_text(doc, model, client, params=params)
        partial_summaries.append(summary)
    
    nb_call_llm = len(partial_summaries)
    logging.info(f"Génération des résumés partiels terminée: {nb_call_llm} appels")
    
    final_summary, nb_call_llm_merge = merge_summaries(partial_summaries, model, client, params=params)
    
    elapsed = time.time() - start_time
    logging.info(f"Traitement terminé en {elapsed:.2f} secondes avec {nb_call_llm + nb_call_llm_merge} appels au total")
    return {"summary": final_summary, "nb_call": nb_call_llm + nb_call_llm_merge}
