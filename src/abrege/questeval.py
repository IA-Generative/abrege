from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from openai import OpenAI

from typing import Literal
import re
import os
import random
import statistics

from abrege.extractive_summary import (
    compute_textrank_score,
    EmbeddingModel,
    text_rank_iterator,
)


import nltk

nltk.download("punkt", quiet=True)


def extract_list(output: str) -> list[str]:
    """Extrait la liste dans une réponse d'un LLM"""
    pattern = r"^(?:[-])|(?:\d+[.])|(?:[*])"
    splitted = [txt.strip() for txt in output.strip().split("\n")]
    selected = [txt for txt in splitted if re.match(pattern, txt)]
    result = [re.sub(pattern, "", txt).strip() for txt in selected]
    assert len(result), f"0 items found in {output=}"
    return result


def qg_model(llm, texts: list[str], n_max_quest: int = 3) -> list[list[str]]:
    assert n_max_quest > 0
    prompt_template = PromptTemplate.from_template(
        """Given the following context text:
```
{context_text}
```
Generate a list of relevant questions that can be answered using the information provided in the context text. Write up to {n_max_quest} questions.

Format your response as follows:

- <question text>
- <question text>
...

Try to generate diverse and thoughtful questions that cover key points and details from the context. Avoid overly broad or vague questions. The answers should be factual and directly reference information from the context text.
""" # noqa
    )
    chain = prompt_template | llm | StrOutputParser() | extract_list
    return [
        chain.invoke({"n_max_quest": n_max_quest, "context_text": text})[
            :n_max_quest
        ]  # [:n_max_quest] on récupère plus de questions que prévu
        for text in texts
    ]


def qa_model(llm, source: str, question: str) -> str:
    assert isinstance(source, str)
    assert isinstance(question, str)
    prompt_template = PromptTemplate.from_template(
        """Given the following context:

{context}

Answer the question based on the information provided in the context above.

Question: {question}

Answer:
"""
    )
    chain = prompt_template | llm | StrOutputParser()
    return chain.invoke({"context": source, "question": question})


def selector(
    list_str: list[str],
    mode: Literal["random", "full", "textrank"],
    k_max: int = 3,
    embedding_model=None,
) -> list[str]:
    assert mode != "textrank" or (embedding_model is not None)
    if k_max > 0:
        k = min(k_max, len(list_str))
    else:
        k = len(list_str)
    if mode == "random":
        selected_sentences = random.sample(list_str, k)
    elif mode == "full":
        selected_sentences = list_str
    elif mode == "textrank":
        idx_generator = text_rank_iterator(list_str, embedding_model)
        selected_idx = [next(idx_generator, None) for _ in range(k)]
        if None in selected_idx:
            # il doit y avoir des doublons dans `list_str`
            pass
        selected_sentences = [
            list_str[idx] for idx in selected_idx if selected_idx is not None
        ]
    else:
        raise NotImplementedError(f"the mode `{mode}`is not implemented")
    return selected_sentences


def f1_bertscore(
    references: list[str], predictions: list[str], lang: str = "en"
) -> float:
    assert len(references) * len(predictions)
    from evaluate import load

    bertscore = load("bertscore")
    results = bertscore.compute(
        predictions=predictions, references=references, lang=lang
    )
    return results["f1"]


def compute_questeval(
    source: str,
    resume: str,
    llm,
    embedding_model=None,
    n_sentence_selected: int = 10,
    n_question_per_sentence: int = 1,
    do_weighter: bool = True,
) -> float:
    assert isinstance(source, str)
    assert isinstance(resume, str)
    assert len(source)
    assert len(resume)

    # Precision part
    sentences = nltk.tokenize.sent_tokenize(source)
    selected_sentences = selector(
        sentences,
        mode="textrank",
        k_max=n_sentence_selected,
        embedding_model=embedding_model,
    )
    selected_questions_unflatten = qg_model(
        llm, selected_sentences, n_max_quest=n_question_per_sentence
    )
    selected_questions = [u for list_ in selected_questions_unflatten for u in list_]
    assert len(selected_questions)
    references = [
        qa_model(llm, source=source, question=question)
        for question in selected_questions
    ]
    predictions = [
        qa_model(llm, source=resume, question=question)
        for question in selected_questions
    ]
    bertscores = f1_bertscore(references=references, predictions=predictions)
    precision = statistics.fmean(bertscores)

    # Recall part
    sentences = nltk.tokenize.sent_tokenize(resume)
    selected_sentences = selector(
        sentences,
        mode="textrank",
        k_max=n_sentence_selected,
        embedding_model=embedding_model,
    )
    selected_questions_unflatten = qg_model(
        llm, selected_sentences, n_max_quest=n_question_per_sentence
    )
    selected_questions = [u for list_ in selected_questions_unflatten for u in list_]
    assert len(selected_questions)

    if do_weighter:
        weights_dict = compute_textrank_score(
            selected_questions, embedding_model
        )  # TODO ici prendre un textrank qui prend de l'anglais
        weights_list = [weights_dict[i] for i in range(len(weights_dict))]
    else:
        weights_list = [1 for _ in selected_questions]
    predictions = [
        qa_model(llm, source=source, question=question)
        for question in selected_questions
    ]
    references = [
        qa_model(llm, source=resume, question=question)
        for question in selected_questions
    ]
    bertscores = f1_bertscore(references=references, predictions=predictions)
    recall = statistics.fmean(bertscores, weights=weights_list)

    f1_score = statistics.harmonic_mean((precision, recall))

    return f1_score


if __name__ == "__main__":
    OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    assert OPENAI_API_BASE and OPENAI_API_KEY
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        temperature=0,
        model="mixtral",
    )

    openai_client = OpenAI(
        api_key=os.environ["OPENAI_EMBEDDING_API_KEY"],
        base_url=os.environ["OPENAI_EMBEDDING_API_BASE"],
    )
    embedding_model = EmbeddingModel(openai_client)
    source = "Alex est en France mais va à l'école en Suisse. Alex est mousquetaire"
    resume = "Alex est l'un des trois mousquetaire"
    score = compute_questeval(
        source=source,
        resume=resume,
        llm=llm,
        embedding_model=embedding_model,
        n_sentence_selected=1,
        n_question_per_sentence=1,
    )
    print()
