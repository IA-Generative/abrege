from typing import List, Optional, Tuple
from openai import OpenAI
import time
import math

from api.utils.logger import logger_abrege as logger_app
from abrege_service.prompts.prompting import generate_prompt
from src.schemas.result import SummaryModel
from src.schemas.task import TaskModel, task_table, TaskStatus, TaskUpdateForm


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


def merge_summaries(
    task: TaskModel,
    summaries: List[str],
    model: str,
    client: OpenAI,
    size: Optional[int] = 300,
    language: Optional[str] = None,
    tempature: Optional[float] = 0.0,
) -> Tuple[TaskModel, int]:
    """
    Combine récursivement les résumés en un seul.
    """
    # Theoretically, the number of calls to the LLM is log2(n) + 1
    nb_call = 0
    total_call = int(math.log(len(summaries), 2)) + 1
    partial_summary: SummaryModel = task.result
    if partial_summary is None:
        partial_summary = SummaryModel(
            created_at=int(time.time()),
            updated_at=int(time.time()),
            summary="",
            word_count=0,
            percentage=0,
            model_name=model,
            model_version=model,
            status=TaskStatus.IN_PROGRESS.value,
            extras={"previous_summary": []},
        )

    while len(summaries) > 1:
        new_summaries = []
        for i in range(0, len(summaries), 2):
            if i + 1 < len(summaries):
                summary1 = summaries[i]
                summary2 = summaries[i + 1]
                previous_summaries = {
                    "sumaries_id": [summary1, summary2],
                    "summaries": [summary1, summary2],
                    "word_count": [len(summary1.split()), len(summary2.split())],
                    "model_name": model,
                    "step": nb_call,
                }

                prompt = generate_prompt(
                    template_name="segement_summary_promt.jinja2",
                    context={
                        "size": size,
                        "language": language,
                        "summaries": [summary1, summary2],
                    },
                )
                t = time.time()
                new_summary = summarize_text(model, client, prompt, temperature=tempature)
                time_merge = time.time() - t
                previous_summaries["time"] = time_merge
                partial_summary.extras["previous_summary"].append(previous_summaries)
                new_summaries.append(new_summary)
                nb_call += 1

                partial_summary.updated_at = int(time.time())
                partial_summary.percentage = nb_call / total_call
                partial_summary.word_count = len(new_summary.split())
                partial_summary.summary = new_summary
                task = task_table.update_task(
                    task_id=task.id,
                    form_data=TaskUpdateForm(
                        status=TaskStatus.IN_PROGRESS.value,
                        result=partial_summary,
                        updated_at=int(time.time()),
                    ),
                )
                logger_app.debug(f"New summary: {new_summary} - Time: {time_merge} - Call: {nb_call}")
            else:
                new_summaries.append(summaries[i])
        summaries = new_summaries

    final_summary = summaries[0]
    partial_summary.updated_at = int(time.time())
    partial_summary.percentage = 1
    partial_summary.word_count = len(final_summary.split())
    partial_summary.summary = final_summary
    task = task_table.update_task(
        task_id=task.id,
        form_data=TaskUpdateForm(
            status=TaskStatus.COMPLETED.value,
            result=partial_summary,
            updated_at=int(time.time()),
        ),
    )
    return task, nb_call
