
import nltk
nltk.download('punkt')
        

from langchain_openai import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import WebBaseLoader
from langchain.prompts import PromptTemplate
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate


from langchain_openai import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import WebBaseLoader
from langchain.prompts import PromptTemplate
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate

from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain



import statistics
from dataclasses import dataclass
from functools import cached_property
import logging

@dataclass
class SelfCheckGPT():
    llm: "Model"
    documents: list
    retriever: "retriever"
    
    @staticmethod
    def parse_response(response:str) -> float:
        response = response.strip().lower()
        if response.startswith("yes"):
            rep_int = 1.
        elif response.startswith("no"):
            rep_int = 0.
        else:
            rep_int = 0.5
            logging.warning(f"The answer given by the LLM is neither yes nor no. We need to review the prompt : {response=}")
        return rep_int

    @staticmethod
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def __post_init__(self):
        template_selfcheck = ("""Is the sentence true, according to the context provided below? Answer only by Yes or No, without justification
####
CONTEXT: {context}

#####
SENTENCE: {text}

Answer:""")
        self.rag_prompt = PromptTemplate.from_template(template_selfcheck)
        self.rag_chain_selfcheck = (
        {"context": self.retriever | SelfCheckGPT.format_docs, "text": RunnablePassthrough()}
        | self.rag_prompt
        | self.llm
        | StrOutputParser())


    def get_array(self, text:str) -> list[int]:
        """Returns a list containing a float for each sentence in text"""
        sentences = nltk.tokenize.sent_tokenize(text)
        responses= [self.rag_chain_selfcheck.invoke(sentence).strip().lower() for sentence in sentences]
        return [SelfCheckGPT.parse_response(r) for r in responses]
    
    def eval_text(self, text:str) -> float:
        """Allows you to evaluate the hallucinations of the text.
        A score close to 0 indicates that the text cannot be justified from the given vecstore.
        On the contrary, a score close to 1 indicates that the information in the text is contained in the given vector store."""
        return statistics.mean(self.get_array(text=text))


def selfcheck(llm: "LLM", docs: list, summarize_to_eval: str) -> float:

    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    from langchain_community.embeddings import HuggingFaceEmbeddings

    from langchain_core.prompts import PromptTemplate

    embeddings = HuggingFaceEmbeddings(model_name="OrdalieTech/Solon-embeddings-base-0.1") # plus de 13 min
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50, keep_separator=True, length_function=len)
    splits = text_splitter.split_documents(docs)
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    selfCheckGPT = SelfCheckGPT(llm, retriever=retriever)

    return selfCheckGPT.eval_text(summarize_to_eval)

if __name__ == "__main__":
    import os
    from pathlib import Path

    OPENAI_API_BASE= os.environ.get("OPENAI_API_BASE", "https://api-ai.numerique-interieur.com/v1") 
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

    llm = ChatOpenAI(api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE, temperature=0, model="mixtral")

    text = Path("./src/camus.txt").read_text()
    documents=[Document(page_content=text)]

    example_summarize = Path("./src/random.txt").read_text()

    metric = selfcheck(llm=llm, docs=documents, summarize_to_eval=example_summarize)
    assert metric <= 0.2

