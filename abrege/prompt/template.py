summarize_template = """
Write a summary of the following text:
{text}
SUMMARY:
"""

map_template = """The following is a set of documents
{docs}
Based on this list of docs, please identify the main themes
Helpful Answer:"""

reduce_template = """The following is set of summaries
{docs}
Take these and distill it into a final, consolidated summary written of the main themes.
Helpful Answer:"""

question_prompt_template = """Write a concise summary of the following :
{text}
CONCISE SUMMARY:"""

refine_template = """
Your job is to produce a final summary
We have provided an existing summary up to a certain point{existing_answer}:
We have the opportunity to refine the existing summary (only if needed)
with some more context below enclosed in triple backstick
´´´{text}´´´
Given the new context, refine the original summary
If the context isn't useful, return the original summary
"""

experimental_map_prompt = """
You will be given a single passage of a document. This section will be enclosed in triple backticks (```)
Your goal is to give a summary of this section so that the reader will have a full understanding fo what happened.
Your response should be at least three paragraphs and fully encopass what was said in the passage.

```{text}```
FULL SUMMARY:
"""  # noqa

experimental_combine_prompt = """
You will be given a series of summaries from a document. The summaries will be enclosed in triple backticks (```)
Your goal is to give a verbose summary of what happened in the document.
The reader should be able to grasp what are the main discussions of the document.

```{text}```
VERBOSE SUMMARY:
"""  # noqa

prompt_template = {
    "summarize": summarize_template,
    "map": map_template,
    "reduce": reduce_template,
    "question": question_prompt_template,
    "refine": refine_template,
}

experimental_prompt_template = {
    "map": experimental_map_prompt,
    "combine": experimental_map_prompt,
}
