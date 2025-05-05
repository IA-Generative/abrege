import nltk


from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from langchain.docstore.document import Document



from typing import Literal
import statistics
from dataclasses import dataclass
import logging
import typing
import random

nltk.download("punkt")

Mode = Literal["full", "random", "textrank"]


@dataclass
class SelfCheckGPT:
    llm: typing.Any
    retriever: typing.Any
    embedding_model: typing.Any

    @staticmethod
    def parse_response(response: str) -> float:
        response = response.strip().lower()
        if response.startswith("yes"):
            rep_int = 1.0
        elif response.startswith("no"):
            rep_int = 0.0
        else:
            rep_int = 0.5
            logging.warning(
                f"""The answer given by the LLM is neither yes nor no. We need to review
                the prompt : {response=}"""
            )
        return rep_int

    @staticmethod
    def format_docs(docs):
        result = "\n\n".join(doc.page_content for doc in docs)
        return result

    def __post_init__(self):
        template_selfcheck = """I'll give you a sentence and a context. Your job is to read the context carefully and the sentence, and determine whether the sentence can be deduced from the context alone. Answer only by Yes or No, without justification
####
CONTEXT: {context}

#####
SENTENCE: {text}

Answer:"""
        self.rag_prompt = PromptTemplate.from_template(template_selfcheck)
        self.rag_chain_selfcheck = (
            {
                "context": self.retriever | SelfCheckGPT.format_docs,
                "text": RunnablePassthrough(),
            }
            | self.rag_prompt
            | self.llm
            | StrOutputParser()
        )

    def get_array(self, text: str, mode: Mode = "full", k_max: int = 5) -> list[float]:
        """Returns a list containing a float for each sentence in text"""
        sentences = nltk.tokenize.sent_tokenize(text)
        if k_max > 0:
            k = min(k_max, len(sentences))
        else:
            k = len(sentences)
        if mode == "random":
            selected_sentences = random.choice(sentences, k)
        elif mode == "full":
            selected_sentences = sentences
        elif mode == "textrank":
            idx_generator = text_rank_iterator(sentences, self.embedding_model)
            selected_idx = [next(idx_generator, None) for _ in range(k)]
            if None in selected_idx:
                # il doit y avoir des doublons dans `sentences`
                pass
            selected_sentences = [
                sentences[idx] for idx in selected_idx if selected_idx is not None
            ]
        else:
            selected_sentences = sentences
            logging.error(f"the mode `{mode}`is not implemented")

        responses = [
            self.rag_chain_selfcheck.invoke(sentence).strip().lower()
            for sentence in selected_sentences
        ]
        return [SelfCheckGPT.parse_response(r) for r in responses]

    def eval_text(self, text: str, mode: Mode = "full", k_max: int = 5) -> float:
        """Allows you to evaluate the hallucinations of the text.
        A score close to 0 indicates that the text cannot be justified from the given
        vecstore.
        On the contrary, a score close to 1 indicates that the information in the text
        is contained in the given vector store.
        """
        return statistics.mean(self.get_array(text=text, mode=mode, k_max=k_max))


def selfcheck(
    llm,
    chroma_embedding,
    embedding_model,
    docs: list,
    summarize_to_eval: str,
    mode: Mode = "full",
    k_max: int = 5,
) -> float:
    """
    embedding_model : une instance de extractive_summary.EmbeddingModel
    docs : une liste des doc représentant le document à résumer
    mode: "full", "textrank" ou "random" Si toutes les phrases du résumé de sont pas à évaluer, quelle phrases traiter en premier ?
    k_max: le nombre de phrase du résumé à évaluer. -1 pour toutes.
    """ # noqa
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=50, keep_separator=True, length_function=len
    )
    splits = text_splitter.split_documents(docs)
    vectorstore = Chroma.from_documents(documents=splits, embedding=chroma_embedding)
    retriever = vectorstore.as_retriever(
        search_type="similarity", search_kwargs={"k": 3}
    )

    selfCheckGPT = SelfCheckGPT(
        llm, retriever=retriever, embedding_model=embedding_model
    )

    return selfCheckGPT.eval_text(summarize_to_eval, mode=mode, k_max=k_max)


if __name__ == "__main__":
    import os
    from pathlib import Path

    OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        temperature=0,
        model="mixtral" if 0 else "qwen2.5",
    )

    #from abrege.summary_chain import (
    #    EmbeddingModel,
    #)
    from openai import OpenAI

    openai_client = OpenAI(
        api_key=os.environ["OPENAI_EMBEDDING_API_KEY"],
        base_url=os.environ["OPENAI_EMBEDDING_API_BASE"],
    )
    embedding_model = None#EmbeddingModel(openai_client)

    #text = Path("./src/camus.txt").read_text()
    #example_summarize = Path("./src/random.txt").read_text()

    text = "Alex est en France mais va à l'école en Suisse. Alex est mousquetaire"
    example_summarize = "Alex est regarde la télévision" if 0 else "Alex est né en Suisse"

    documents = [Document(page_content=text)]

    if 1:
        from langchain_huggingface import HuggingFaceEmbeddings

        chroma_embedding = HuggingFaceEmbeddings(
            model_name="OrdalieTech/Solon-embeddings-base-0.1"
        )  # plus de 13 min
    else:
        from chromadb.utils import embedding_functions
        chroma_embedding = embedding_functions.DefaultEmbeddingFunction()

    metric = selfcheck(
        llm=llm,
        chroma_embedding=chroma_embedding,
        embedding_model=embedding_model,
        docs=documents,
        summarize_to_eval=example_summarize,
    )
    assert metric <= 0.2
    print(metric)
