from utils.pdf_handler import ModeOCR, OCRPdfLoader
from typing import Annotated, get_args, List
import requests
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
import tempfile
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import StreamingResponse
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredODTLoader,
    Docx2txtLoader,
    UnstructuredURLLoader,
    TextLoader,
    # SeleniumURLLoader
)
from abrege.summary_chain import (
    summarize_chain_builder,
    EmbeddingModel,
    prompt_template,
)
import sys
import nltk


def chat_builder(openai_key: str, openai_api_base: str,  model_id: List[str], model: str = "phi3", temperature: int = 0):
    if model not in model_id:
        raise HTTPException(
            400, detail=f"Model not available, avaible are {model_id}"
        )
    llm = ChatOpenAI(
        api_key=openai_key,
        openai_api_base=openai_api_base,
        model=model,
        temperature=temperature,
        max_retries=10,
    )
    return llm


class Summarizer:
    def __init__(self, openai_key: str, openai_api_base: str, models: List[str], embedding_model):
        self.openai_key = openai_key
        self.openai_api_base = openai_api_base
        self.models = models
        self.embedding_model = embedding_model

    def set_chat(self, model_name: str, temperature:  float) -> ChatOpenAI:

        return chat_builder(openai_key=self.openai_key, openai_api_base=self.openai_api_base,
                            model=model_name,  model_id=self.models, temperature=temperature)

    def set_custom_chain(self, llm: ChatOpenAI, method: str, context_size: int, size: int, language: str,
                         summarize_template: str,
                         map_template: str,
                         reduce_template: str,
                         question_template: str,
                         refine_template: str,
                         custom_prompt: str):
        return summarize_chain_builder(
            llm=llm,
            embedding_model=self.embedding_model,
            method=method,
            context_size=context_size,
            language=language,
            size=size,
            summarize_template=summarize_template,
            map_template=map_template,
            reduce_template=reduce_template,
            question_template=question_template,
            refine_template=refine_template,
            custom_prompt=custom_prompt,
        )

    def get_custom_model(self, model_name: str, temperature:  float, method: str, context_size: int, size: int, language: str,
                         summarize_template: str,
                         map_template: str,
                         reduce_template: str,
                         question_template: str,
                         refine_template: str,
                         custom_prompt: str):

        llm = self.set_chat(model_name=model_name, temperature=temperature)
        return self.set_custom_chain(llm=llm, method=method, context_size=context_size, size=size, language=language,
                                     summarize_template=summarize_template, map_template=map_template, reduce_template=reduce_template,
                                     question_template=question_template, refine_template=refine_template, custom_prompt=custom_prompt)
