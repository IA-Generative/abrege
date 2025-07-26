from typing import List, Optional
from openai import OpenAI
import time
import math
import hashlib
import os

from src.utils.logger import logger_abrege as logger_app
from abrege_service.prompts.prompting import generate_prompt
from src.schemas.result import SummaryModel, Text, PartialSummary
from src.schemas.task import TaskModel, TaskStatus
from src.schemas.parameters import SummaryParameters
from abrege_service.models.base import BaseSummaryService
from abrege_service.utils.text import split_texts_by_token_limit
from abrege_service.config.openai import OpenAISettings

openai_settings = OpenAISettings()


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
        params = task.parameters
        if task.parameters is None:
            params = SummaryParameters(size=self.size, language=self.language, temperature=self.temperature)

        # Theoretically, the number of calls to the LLM is log2(n) + 1 if not odds
        task_id = task.id
        nb_call = 0
        logger_app.info(f"Start task {task_id} - nb texts {len(task.output.texts_found)}")
        logger_app.info(
            f"task {task_id} - MAX_CONTEXT_SIZE {openai_settings.MAX_CONTEXT_SIZE * 0.75} - MODEL {openai_settings.TOKENIZER_MODEL_NAME} "
        )

        splitted_text = split_texts_by_token_limit(
            task.output.texts_found,
            max_tokens=int(openai_settings.MAX_CONTEXT_SIZE * 0.75),  # Secure number of token
            model=openai_settings.TOKENIZER_MODEL_NAME,
            cache_dir=os.environ.get("CACHE_FOLDER"),
        )
        task.output.texts_found = splitted_text
        logger_app.info(f"Start task {task_id} - nb texts {len(splitted_text)} -- ")
        total_call = int(math.log(len(task.output.texts_found), 2)) + 1 + 1 if params.custom_prompt else 0
        logger_app.info(f"Start task {task_id} - theory nb calls {total_call} - nb texts {len(task.output.texts_found)}")
        t_start = time.time()
        task.output = SummaryModel(
            created_at=task.output.created_at,
            updated_at=int(time.time()),
            summary="",
            word_count=0,
            percentage=0,
            model_name=self.model_name,
            model_version=self.model_name,
            status=TaskStatus.IN_PROGRESS.value,
            texts_found=task.output.texts_found,
            extras={},
        )

        texts = [
            Text(
                id=hashlib.md5(item.encode()).hexdigest(),
                text=item,
                word_count=len(item.split()),
            )
            for item in task.output.texts_found
        ]
        task.output.partial_summaries = texts
        if len(texts) == 1:
            logger_app.info(f"task {task_id} - only one text detected")
            prompt = generate_prompt(
                template_name="segement_summary_promt.jinja2",
                context={
                    "size": params.size,
                    "language": params.language,
                    "text": texts[0].text,
                },
            )
            summary = summarize_text(self.model_name, self.client, prompt=prompt)
            task.output.summary = summary
            task.output.word_count = len(summary.split())
            task.output.percentage = 1
            task.output.nb_llm_calls = 1
            task = self.update_result_task(
                task=task,
                result=task.output,
                status=TaskStatus.COMPLETED.value,
                percentage=1,
            )
            logger_app.info(f"task {task_id} - Done {time.time() - t_start}")
            return task

        task = self.update_result_task(task=task, result=task.output, status=TaskStatus.IN_PROGRESS.value)
        start_size = len(texts)
        previous_percentage = task.percentage
        left_percentage = 1 - previous_percentage

        while len(texts) > 1:
            logger_app.info(f"task {task_id} - {len(texts)}/{start_size} process")
            new_summaries: List[Text] = []
            logger_app.info(79 * "*")
            for i in range(0, len(texts), 2):
                logger_app.info(f"task {task_id} [{i}:{i + 1}]({len(texts)}) start")
                if i + 1 < len(texts):
                    summary1 = texts[i].text
                    summary2 = texts[i + 1].text

                    prompt = generate_prompt(
                        template_name="final_summary_prompt.jinja2",
                        context={
                            "size": params.size,
                            "language": params.language,
                            "summaries": [summary1, summary2],
                        },
                    )
                    t = time.time()
                    new_summary = summarize_text(
                        self.model_name,
                        self.client,
                        prompt,
                        temperature=self.temperature,
                    )
                    word_count = len(new_summary.split())
                    partial_sum = PartialSummary(
                        id=hashlib.md5(new_summary.encode()).hexdigest(),
                        text=new_summary,
                        word_count=word_count,
                        text1=texts[i],
                        text2=texts[i + 1],
                    )
                    task.output.partial_summaries.append(partial_sum)
                    time_merge = time.time() - t

                    new_summaries.append(partial_sum)
                    nb_call += 1

                    task.output.updated_at = int(time.time())
                    task.output.nb_llm_calls = nb_call
                    task.output.percentage = nb_call / total_call
                    task.output.word_count = word_count
                    task.output.summary = new_summary

                    logger_app.debug(f"task {task_id} [{i}:{i + 1}]({len(texts)}), Time: {time_merge} - Call: {nb_call}/ {total_call}")
                    task = self.update_result_task(
                        task=task,
                        result=task.output,
                        status=TaskStatus.IN_PROGRESS.value,
                        percentage=previous_percentage + left_percentage * task.output.percentage,
                    )
                    logger_app.debug(f"task {task_id} - partial saved")
                else:
                    logger_app.debug(f"task {task_id} [{i}]({len(texts)})")
                    new_summaries.append(texts[i])
            logger_app.info(79 * "*")

            texts = new_summaries
            logger_app.info(f"task {task_id} - {nb_call} calls - {total_call} - {len(texts)}")

        assert len(texts) == 1, f"Final text should be only one item with the summary - nb texts {len(texts)} we get "
        final_summary = texts[0]
        if params.custom_prompt:
            logger_app.debug(f"{task_id} - use custom prompt")
            prompt = generate_prompt(
                template_name="custom_prompt.jinja2",
                context={
                    "size": params.size,
                    "language": params.language,
                    "summary": final_summary,
                    "custom_prompt": params.custom_prompt,
                },
            )
            final_summary = summarize_text(self.model_name, self.client, prompt=prompt)
        task.output.updated_at = int(time.time())
        task.output.percentage = 1
        task.output.word_count = len(final_summary.text.split())
        task.output.summary = final_summary.text
        task = self.update_result_task(
            task=task,
            result=task.output,
            status=TaskStatus.COMPLETED.value,
            percentage=1,
        )
        return task
