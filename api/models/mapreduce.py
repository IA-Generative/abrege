import operator
from time import perf_counter
import logging
import traceback
from typing import Annotated, List, Literal, TypedDict
import asyncio
from config.openai import OpenAISettings
from fastapi import HTTPException

from openai import OpenAI
import openai

from langchain.chains.combine_documents.reduce import (
    acollapse_docs,
    split_list_of_docs,
)
from langchain_core.documents import Document
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph

from langchain_openai import ChatOpenAI

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from schemas.params import ParamsSummarize
from schemas.response import SummaryResponse

client = OpenAI(api_key=OpenAISettings().OPENAI_API_KEY, base_url=OpenAISettings().OPENAI_API_BASE)


async def do_map_reduce(
    list_str: list[str], params: ParamsSummarize, recursion_limit: int = 20, num_tokens_limit: int = 1226 * 300
) -> SummaryResponse:
    """Peut faire un GraphRecursionError si recursion_limit est trop faible"""

    deb = perf_counter()
    logging.info(f"Début du processus de map-reduce avec {len(list_str)} documents")
    
    llm = ChatOpenAI(
        model=params.model, temperature=params.temperature, api_key=OpenAISettings().OPENAI_API_KEY, base_url=OpenAISettings().OPENAI_API_BASE
    )

    num_tokens = llm.get_num_tokens(" ".join(list_str))
    logging.info(f"Nombre total de tokens: {num_tokens}")

    if num_tokens > num_tokens_limit:
        logging.error(f"Limite de tokens dépassée: {num_tokens} > {num_tokens_limit}")
        raise HTTPException(
            status_code=500,
            detail=f"Le texte à résumer est trop long. (environ {num_tokens} tokens alors que la limite est à {num_tokens_limit} tokens)",
        )

    token_max = int(params.context_size)
    logging.info(f"Taille maximale de contexte: {token_max} tokens")

    try:
        # On vérifie qu'il y a bien une balise {context} dans params.map_prompt et pas d'autres balises
        params.map_prompt.format(context="placeholder")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail='Erreur lors de l\'utilisation du prompt "map_prompt". map_prompt ne peut pas contenir une balise autre que {context}',
        )

    map_prompt = ChatPromptTemplate.from_messages([("human", params.map_prompt)])

    map_chain = map_prompt | llm | StrOutputParser()

    try:
        reduce_template = params.reduce_prompt.format(language=params.language, size=str(params.size), docs="{docs}")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail='Erreur lors de l\'utilisation du prompt "reduce_prompt". reduce_prompt ne peut pas contenir une balise autre que {language}, {size} ou {docs}',
        )
    if params.custom_prompt is not None:
        reduce_template += params.custom_prompt

    reduce_prompt = ChatPromptTemplate([("human", reduce_template)])

    reduce_chain = reduce_prompt | llm | StrOutputParser()

    def length_function(documents: List[Document]) -> int:
        """Get number of tokens for input contents."""
        return sum(llm.get_num_tokens(doc.page_content) for doc in documents)

    # This will be the overall state of the main graph.
    # It will contain the input document contents, corresponding
    # summaries, and a final summary.
    class OverallState(TypedDict):
        # Notice here we use the operator.add
        # This is because we want combine all the summaries we generate
        # from individual nodes back into one list - this is essentially
        # the "reduce" part
        contents: List[str]
        summaries: Annotated[list, operator.add]
        collapsed_summaries: List[Document]
        final_summary: str

    # This will be the state of the node that we will "map" all
    # documents to in order to generate summaries
    class SummaryState(TypedDict):
        content: str

    # Here we generate a summary, given a document
    async def generate_summary(state: SummaryState):
        logging.debug(f"Génération du résumé pour un document de {len(state['content'])} caractères")
        response = await map_chain.ainvoke(state["content"])
        logging.debug("Résumé généré avec succès")
        return {"summaries": [response]}

    # Here we define the logic to map out over the documents
    # We will use this an edge in the graph
    def map_summaries(state: OverallState):
        # We will return a list of `Send` objects
        # Each `Send` object consists of the name of a node in the graph
        # as well as the state to send to that node
        return [Send("generate_summary", {"content": content}) for content in state["contents"]]

    def collect_summaries(state: OverallState):
        return {"collapsed_summaries": [Document(summary) for summary in state["summaries"]]}

    # Add node to collapse summaries
    async def collapse_summaries(state: OverallState):
        logging.info(f"Collapse des {len(state['collapsed_summaries'])} résumés")
        doc_lists = split_list_of_docs(state["collapsed_summaries"], length_function, token_max)
        logging.info(f"Résumés divisés en {len(doc_lists)} groupes")
        results = []
        for i, doc_list in enumerate(doc_lists):
            logging.debug(f"Traitement du groupe {i+1}/{len(doc_lists)}")
            results.append(await acollapse_docs(doc_list, reduce_chain.ainvoke))
        logging.info("Collapse des résumés terminé")
        return {"collapsed_summaries": results}

    # This represents a conditional edge in the graph that determines
    # if we should collapse the summaries or not
    def should_collapse(
        state: OverallState,
    ) -> Literal["collapse_summaries", "generate_final_summary"]:
        num_tokens = length_function(state["collapsed_summaries"])
        if num_tokens > token_max:
            return "collapse_summaries"
        else:
            return "generate_final_summary"

    # Here we will generate the final summary
    async def generate_final_summary(state: OverallState):
        response = await reduce_chain.ainvoke(state["collapsed_summaries"])
        return {"final_summary": response}

    # Construct the graph
    # Nodes:
    graph = StateGraph(OverallState)
    graph.add_node("generate_summary", generate_summary)  # same as before
    graph.add_node("collect_summaries", collect_summaries)
    graph.add_node("collapse_summaries", collapse_summaries)
    graph.add_node("generate_final_summary", generate_final_summary)

    # Edges:
    graph.add_conditional_edges(START, map_summaries, ["generate_summary"])
    graph.add_edge("generate_summary", "collect_summaries")
    graph.add_conditional_edges("collect_summaries", should_collapse)
    graph.add_conditional_edges("collapse_summaries", should_collapse)
    graph.add_edge("generate_final_summary", END)

    app = graph.compile()

    try:
        nb_call = 0
        logging.info("Démarrage de l'exécution du graphe")
        async for step in app.astream(
            {"contents": list_str},
            {"recursion_limit": recursion_limit},
        ):
            nb_call += 1
            logging.debug(f"Étape {nb_call} du graphe exécutée")
    except openai.InternalServerError as e:
        logging.error(f"Erreur interne OpenAI: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=429,
            detail="Surcharge du LLM",
        )
    except openai.RateLimitError as e:
        logging.error(f"Erreur de limite de taux OpenAI: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=429,
            detail="Surcharge du LLM",
        )

    elapsed = perf_counter() - deb
    logging.info(f"Processus de map-reduce terminé en {elapsed:.2f} secondes avec {nb_call} appels")

    final_summary = step["generate_final_summary"]["final_summary"]
    logging.info(f"Résumé final généré avec {len(final_summary)} caractères")

    return SummaryResponse(summary=final_summary, nb_call=nb_call, time=elapsed)
