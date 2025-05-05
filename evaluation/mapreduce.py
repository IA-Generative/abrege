import logging
import operator
import os
import traceback
from time import perf_counter
from typing import Annotated, List, Literal, TypedDict

import openai
from fastapi import HTTPException, Query
from langchain.chains.combine_documents.reduce import (
    acollapse_docs,
    split_list_of_docs,
)
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from openai import OpenAI
from pydantic import BaseModel

MethodType = Literal["map_reduce", "refine", "text_rank", "k-means", "stuff"]  # "text_rank2", "k-means2"
ChunkType = Literal["sentences", "chunks"]

MAP_PROMPT = "Rédigez un résumé concis des éléments suivants :\\n\\n{context}"
REDUCE_PROMPT = """
Voici une série de résumés:
{docs}
Rassemblez ces éléments et faites-en un résumé final et consolidé dans {language} en {size} mots au maximum. Rédigez uniquement en {language}.
"""


class ParamsSummarize(BaseModel):
    method: MethodType | None = "map_reduce"
    model: str = os.environ["OPENAI_API_MODEL"]
    context_size: int | None = 16_000
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0.0
    language: str | None = "French"
    size: int | None = 4_000
    # summarize_template: str | None = (None,)
    # map_template: str | None = (None,)
    # reduce_template: str | None = (None,)
    # question_template: str | None = (None,)
    # refine_template: str | None = (None,)
    custom_prompt: str | None = None  # param déprécié
    map_prompt: str = MAP_PROMPT
    reduce_prompt: str = REDUCE_PROMPT




class SummaryResponse(BaseModel):
    summary: str
    nb_call: int | None = None
    time: float | None = None


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"])


async def do_map_reduce(
    list_str: list[str], params: ParamsSummarize, recursion_limit: int = 20, num_tokens_limit: int = 1226 * 300, max_concurrency: int = 15
) -> SummaryResponse:
    """Peut faire un GraphRecursionError si recursion_limit est trop faible"""

    deb = perf_counter()
    llm = ChatOpenAI(model=params.model, temperature=params.temperature, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"])

    concat_str = [list_str[0]]
    for index, str_ in enumerate(list_str[1:]):
        candidat = concat_str[-1] + "\n---\n" + str_
        if llm.get_num_tokens(candidat) > params.context_size:
            concat_str.append(str_)
        else:
            concat_str[-1] = candidat

    num_tokens = llm.get_num_tokens(" ".join(list_str))

    if num_tokens > num_tokens_limit:
        raise HTTPException(
            status_code=500,
            detail=f"Le texte à résumer est trop long. (environ {num_tokens} tokens alors que la limite est à {num_tokens_limit} tokens)",
        )

    token_max = int(params.context_size)

    try:
        # On vérifie qu'il y a bien une balise {context} dans params.map_prompt et pas d'autres balises
        params.map_prompt.format(context="placeholder")
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Erreur lors de l\'utilisation du prompt "map_prompt". map_prompt ne peut pas contenir une balise autre que {context}',
        )

    map_prompt = ChatPromptTemplate.from_messages([("human", params.map_prompt)])

    map_chain = map_prompt | llm | StrOutputParser()
    size = min(params.size, len(" ".join(list_str).split(" ")))
    try:
        reduce_template = params.reduce_prompt.format(language=params.language, size=str(size), docs="{docs}")
    except Exception:
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
        response = await map_chain.ainvoke(state["content"])
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
        doc_lists = split_list_of_docs(state["collapsed_summaries"], length_function, token_max)
        results = []
        for doc_list in doc_lists:
            results.append(await acollapse_docs(doc_list, reduce_chain.ainvoke))

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
        async for step in app.astream(
            # {"contents": [doc.page_content for doc in split_docs]},
            {"contents": list_str if 0 else concat_str},
            {"recursion_limit": recursion_limit, "max_concurrency": max_concurrency},
        ):
            # print(list(step.keys()))
            list(step.keys())
            nb_call += 1
    except openai.InternalServerError as e:
        logging.error(f"{e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=429,
            detail="Surcharge du LLM",
        )
    except openai.RateLimitError as e:
        logging.error(f"{e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=429,
            detail="Surcharge du LLM",
        )

    elapsed = perf_counter() - deb

    final_summary = step["generate_final_summary"]["final_summary"]

    return SummaryResponse(summary=final_summary, nb_call=nb_call, time=elapsed)
