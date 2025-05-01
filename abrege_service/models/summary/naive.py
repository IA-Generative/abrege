from typing import List, Optional
from openai import OpenAI
import time
import math
import hashlib

from src.utils.logger import logger_abrege as logger_app
from abrege_service.prompts.prompting import generate_prompt
from src.schemas.result import SummaryModel, Text, PartialSummary
from src.schemas.task import TaskModel, TaskStatus
from abrege_service.models.base import BaseSummaryService


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


class NaiveSummaryService(BaseSummaryService):
    def __init__(
        self,
        model_name: str,
        client: OpenAI,
        size: Optional[int] = 300,
        language: Optional[str] = None,
        temperature: Optional[float] = 0.0,
    ):
        super().__init__()

        self.model_name = model_name
        self.client = client
        self.size = size
        self.language = language
        self.temperature = temperature

    def summarize(self, task: TaskModel, *args, **kwargs) -> TaskModel:
        # Theoretically, the number of calls to the LLM is log2(n) + 1 if not odds
        nb_call = 0
        total_call = int(math.log(len(task.result.texts_found), 2)) + 1
        task.result = SummaryModel(
            created_at=task.result.created_at,
            updated_at=int(time.time()),
            summary="",
            word_count=0,
            percentage=0,
            model_name=self.model_name,
            model_version=self.model_name,
            status=TaskStatus.IN_PROGRESS.value,
            texts_found=task.result.texts_found,
            extras={},
        )

        texts = [Text(id=hashlib.md5(item.encode()).hexdigest(), text=item, word_count=len(item.split())) for item in task.result.texts_found]
        task.result.partial_summaries = texts
        if len(texts) == 1:
            prompt = generate_prompt(
                template_name="segement_summary_promt.jinja2",
                context={
                    "size": self.size,
                    "language": self.language,
                    "text": texts[0].text,
                },
            )
            summary = summarize_text(self.model_name, self.client, prompt=prompt)
            task.result.summary = summary
            task.result.word_count = len(summary.split())
            task.result.percentage = 1
            task.result.nb_llm_calls = 1
            task = self.update_result_task(task=task, result=task.result, status=TaskStatus.COMPLETED.value)

            return task

        task = self.update_result_task(task=task, result=task.result, status=TaskStatus.IN_PROGRESS.value)

        while len(texts) > 1:
            new_summaries: List[Text] = []
            for i in range(0, len(texts), 2):
                if i + 1 < len(texts):
                    summary1 = texts[i].text
                    summary2 = texts[i + 1].text

                    prompt = generate_prompt(
                        template_name="final_summary_prompt.jinja2",
                        context={
                            "size": self.size,
                            "language": self.language,
                            "summaries": [summary1, summary2],
                        },
                    )
                    t = time.time()
                    new_summary = summarize_text(self.model_name, self.client, prompt, temperature=self.temperature)
                    word_count = len(new_summary.split())
                    partial_sum = PartialSummary(
                        id=hashlib.md5(new_summary.encode()).hexdigest(), text=new_summary, word_count=word_count, text1=texts[i], text2=texts[i + 1]
                    )
                    task.result.partial_summaries.append(partial_sum)
                    time_merge = time.time() - t

                    new_summaries.append(partial_sum)
                    nb_call += 1

                    task.result.updated_at = int(time.time())
                    task.result.nb_llm_calls = nb_call
                    task.result.percentage = nb_call / total_call
                    task.result.word_count = word_count
                    task.result.summary = new_summary

                    logger_app.debug(f"New summary: {new_summary} - Time: {time_merge} - Call: {nb_call}")
                    task = self.update_result_task(task=task, result=task.result, status=TaskStatus.IN_PROGRESS.value)
                else:
                    new_summaries.append(texts[i])
            texts = new_summaries

        assert len(texts) == 1, f"Final text should be only one item with the summary - nb texts {len(texts)} we get "
        final_summary = texts[0]
        task.result.updated_at = int(time.time())
        task.result.percentage = 1
        task.result.word_count = len(final_summary.text.split())
        task.result.summary = final_summary.text
        task = self.update_result_task(task=task, result=task.result, status=TaskStatus.COMPLETED.value)
        return task
