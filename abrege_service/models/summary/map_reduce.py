import os
import time
import operator
from time import perf_counter
import logging
import traceback
import hashlib
from typing import Annotated, List, Literal, TypedDict

import openai

from langchain.chains.combine_documents.reduce import (
    collapse_docs,
    split_list_of_docs,
)
from langchain_core.documents import Document
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph

from langchain_openai import ChatOpenAI

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from abrege_service.models.base import BaseSummaryService
from src.schemas.result import SummaryModel, Text
from src.schemas.task import TaskModel, TaskStatus


from abrege_service.utils.text import split_texts_by_word_limit
from src.utils.logger import logger_abrege
import nltk

nltk_data_dir = os.environ.get("NLTK_DATA", "/app/.cache/nltk_data")
nltk.download("averaged_perceptron_tagger_eng", download_dir=nltk_data_dir)
nltk.download("punkt_tab", download_dir=nltk_data_dir)

nltk.data.path.append(nltk_data_dir)


class LangChainMapReduceService(BaseSummaryService):
    def __init__(
        self,
        llm: ChatOpenAI,
        ratio_word_token=0.75,
        num_tokens_limit=128_000,
        recursion_limit=20,
    ):
        super().__init__()
        self.llm = llm
        self.ratio_word_token = ratio_word_token
        self.num_tokens_limit = num_tokens_limit
        self.recursion_limit = recursion_limit

    def summarize(self, task: TaskModel, *args, **kwargs) -> TaskModel:
        task.result = SummaryModel(
            created_at=task.result.created_at,
            updated_at=int(time.time()),
            summary="",
            word_count=0,
            percentage=0,
            model_name=self.llm.model_name,
            model_version=self.llm.model_name,
            status=TaskStatus.IN_PROGRESS.value,
            texts_found=task.result.texts_found,
            extras={},
        )

        params = task.parameters

        deb = perf_counter()

        logger_abrege.info(f"Début du processus de map-reduce avec {len(task.result.texts_found)} documents")

        for i, text in enumerate(task.result.texts_found):
            num_tokens = self.llm.get_num_tokens(text)
            logger_abrege.info(f"Before optim : Danse la page {i + 1} Nombre de tokens: {num_tokens}")

        list_str = split_texts_by_word_limit(
            texts=task.result.texts_found,
            max_words=int(self.num_tokens_limit * self.ratio_word_token),
        )
        for i, text in enumerate(list_str):
            num_tokens = self.llm.get_num_tokens(text)
            logger_abrege.info(f"After optim : Danse la page {i + 1} Nombre de tokens: {num_tokens}")

        task.result.texts_found = list_str
        task = self.update_result_task(task=task, result=task.result, status=TaskStatus.IN_PROGRESS.value)

        logger_abrege.info(f"Taille maximale de contexte: {self.num_tokens_limit} tokens")

        try:
            # On vérifie qu'il y a bien une balise {context} dans params.map_prompt et pas d'autres balises
            params.map_prompt.format(context="placeholder")
        except Exception as e:
            logger_abrege.error(traceback.format_exc())
            raise e

        map_prompt = ChatPromptTemplate.from_messages([("human", params.map_prompt)])

        map_chain = map_prompt | self.llm | StrOutputParser()

        try:
            reduce_template = params.reduce_prompt.format(language=params.language, docs="{docs}", size=params.size)
        except Exception as e:
            logger_abrege.error(traceback.format_exc())
            raise e
        if params.custom_prompt is not None:
            reduce_template += params.custom_prompt

        reduce_prompt = ChatPromptTemplate([("human", reduce_template)])

        reduce_chain = reduce_prompt | self.llm | StrOutputParser()

        def length_function(documents: List[Document]) -> int:
            """Get number of tokens for input contents."""
            return sum(self.llm.get_num_tokens(doc.page_content) for doc in documents)

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
        def generate_summary(state: SummaryState):
            logger_abrege.debug(f"Génération du résumé pour un document de {len(state['content'])} caractères")
            response = map_chain.invoke(state["content"])
            logger_abrege.debug("Résumé généré avec succès")
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
        def collapse_summaries(state: OverallState):
            logger_abrege.info(f"Collapse des {len(state['collapsed_summaries'])} résumés")
            doc_lists = split_list_of_docs(state["collapsed_summaries"], length_function, self.num_tokens_limit)
            logger_abrege.info(f"Résumés divisés en {len(doc_lists)} groupes")
            results = []
            for i, doc_list in enumerate(doc_lists):
                logger_abrege.debug(f"Traitement du groupe {i + 1}/{len(doc_lists)}")
                results.append(collapse_docs(doc_list, reduce_chain.invoke))
            logger_abrege.info("Collapse des résumés terminé")
            return {"collapsed_summaries": results}

        # This represents a conditional edge in the graph that determines
        # if we should collapse the summaries or not
        def should_collapse(
            state: OverallState,
        ) -> Literal["collapse_summaries", "generate_final_summary"]:
            num_tokens = length_function(state["collapsed_summaries"])
            if num_tokens > self.num_tokens_limit:
                return "collapse_summaries"
            else:
                return "generate_final_summary"

        # Here we will generate the final summary
        def generate_final_summary(state: OverallState):
            response = reduce_chain.invoke(state["collapsed_summaries"])
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
            logger_abrege.info("Démarrage de l'exécution du graphe")
            result = app.invoke(
                {"contents": list_str},
                {"recursion_limit": self.recursion_limit},
                # debug=logger_abrege.level == logging.DEBUG,
            )
            for step in result:
                nb_call += 1
                task.result.nb_llm_calls = nb_call
                task.result.percentage = 0.7  # How to calculate correctly ?
                for item in result[step]:
                    if isinstance(item, str):
                        text = Text(
                            id=hashlib.md5(item.encode()).hexdigest(),
                            text=item,
                            word_count=len(item.split()),
                        )
                        task.result.partial_summaries.append(text)
                    if isinstance(item, list):
                        for unit_item in item:
                            if isinstance(unit_item, str):
                                text = Text(
                                    id=hashlib.md5(unit_item.encode()).hexdigest(),
                                    text=unit_item,
                                    word_count=len(unit_item.split()),
                                )
                                task.result.partial_summaries.append(text)
                            if isinstance(unit_item, Document):
                                tmp_text = unit_item.page_content
                                text = Text(
                                    id=hashlib.md5(tmp_text.encode()).hexdigest(),
                                    text=tmp_text,
                                    word_count=len(tmp_text.split()),
                                )
                                task.result.partial_summaries.append(text)

                task = self.update_result_task(task=task, result=task.result, status=TaskStatus.IN_PROGRESS.value)

                logger_abrege.debug(f"Étape {nb_call} du graphe exécutée")
                elapsed = perf_counter() - deb
                logger_abrege.info(f"Processus de map-reduce terminé en {elapsed:.2f} secondes avec {nb_call} appels")

                task.result.summary = result["final_summary"]
                task.result.word_count = len(result["final_summary"].split())
                task.result.percentage = 1

                logger_abrege.info(f"Résumé final généré avec {len(task.result.summary)} caractères - nb words {task.result.word_count}")
                self.update_result_task(task=task, result=task.result, status=TaskStatus.COMPLETED.value)
                return task

        except openai.InternalServerError as e:
            logging.error(f"Erreur interne OpenAI: {e}\n{traceback.format_exc()}")
            return self.update_result_task(task=task, status=TaskStatus.FAILED.value)

        except openai.RateLimitError as e:
            logger_abrege.error(traceback.format_exc())

            logger_abrege.error(f"Erreur de limite de taux OpenAI: {e}\n{traceback.format_exc()}")
            return self.update_result_task(task=task, status=TaskStatus.FAILED.value)
