# abrege-sdk

Python client for the Abrège API - sync (`SyncAbregeClient`) and async (`AsyncAbregeClient`),
with the same methods on both.

## Installation

Not published to PyPI yet - install straight from this repo, either as an editable local
path (if you have the monorepo checked out) or as a git dependency:

```bash
# From a local checkout
uv add --editable ./sdk/python
# or
pip install -e ./sdk/python
```

```bash
# As a git dependency, pinned to a subdirectory
uv add "abrege-sdk @ git+https://github.com/IA-Generative/abrege.git#subdirectory=sdk/python"
```

## Quickstart

```python
from abrege_sdk.client_sync import SyncAbregeClient
from abrege_sdk.schemas.content import Input, TextContent

with SyncAbregeClient("http://localhost:5000/api", api_key="...") as client:
    task = client.summarize_text(Input(content=TextContent(text="Some long text to summarize...")))
    task = client.wait_for_task(task.id)
    print(task.output.summary)
```

`base_url` is the API's own base URL - `/api` included, since every route lives under it (see
[docs/routes.md](../../docs/routes.md) for the full list, or `<base_url>/docs` for interactive
Swagger docs served by a running instance).

The async client mirrors this one method-for-method:

```python
import asyncio
from abrege_sdk.client_async import AsyncAbregeClient
from abrege_sdk.schemas.content import Input, TextContent


async def main():
    async with AsyncAbregeClient("http://localhost:5000/api", api_key="...") as client:
        task = await client.summarize_text(Input(content=TextContent(text="...")))
        task = await client.wait_for_task(task.id)
        print(task.output.summary)


asyncio.run(main())
```

## Authentication

Two ways to authenticate:

**Static API key** (e.g. a Keycloak service-account token):

```python
from abrege_sdk.client_sync import SyncAbregeClient

with SyncAbregeClient("http://localhost:5000/api", api_key="...") as client:
    ...
```

**Username/password** (real user identity, via Keycloak Resource Owner Password
Credentials grant - the Keycloak client secret never leaves the backend):

```python
with SyncAbregeClient("http://localhost:5000/api") as client:
    client.login("user@example.com", "hunter2")
    ...
```

`login()` also stores a refresh token; subsequent requests renew the access token
automatically as it nears expiry (`client.refresh_access_token()` to force it early).

## Tasks

A "task" is an async summarization job: you create one from text, a URL, or a document, then
poll it (or use `wait_for_task`) until it completes.

```python
from abrege_sdk.schemas.content import Input, TextContent, UrlContent
from abrege_sdk.schemas.parameters import SummaryParameters

# From raw text
task = client.summarize_text(Input(content=TextContent(text="...")))

# From a URL
task = client.summarize_text(Input(content=UrlContent(url="https://example.com/article")))

# From a file
task = client.summarize_doc("report.pdf")

# Custom summary parameters (language, size, method, custom prompt...)
task = client.summarize_text(Input(
    content=TextContent(text="..."),
    parameters=SummaryParameters(language="English", size=200),
))

task = client.wait_for_task(task.id)            # blocks until completed/failed
task = client.get_task(task.id)                 # one-shot status check
text = client.get_task_text(task.id)            # convenience over task.output.summary
page = client.get_user_tasks(page=1, page_size=10)
client.cancel_task(task.id)
client.delete_task(task.id)
```

### Optional side extractions

Beyond the summary, four extra extractions can each be requested independently - all `False`
by default, so a summary costs nothing extra unless asked for:

```python
task = client.summarize_text(Input(
    content=TextContent(text="..."),
    parameters=SummaryParameters(
        extract_qa=True,        # question/answer pairs grounded in the source text
        extract_entities=True,  # entities and their relationships
        extract_chunks=True,    # the semantic sub-chunks the summary was built from
        classify_topics=True,   # free-form topic classification of the final summary
    ),
))
```

Each runs decoupled from the summary itself (see
[docs/document-insights.md](../../docs/document-insights.md)), and only what was requested is
persisted - `task.parameters` on the response tells you which.

## Error handling

All SDK-raised errors subclass `AbregeSDKError` (`abrege_sdk.exceptions`):

```python
from abrege_sdk.exceptions import AbregeAPIError, AbregeAuthenticationError, AbregeTimeoutError

try:
    task = client.wait_for_task(task.id, max_wait_time=60.0)
except AbregeAuthenticationError:
    ...  # login()/token rejected, or refresh token expired
except AbregeTimeoutError:
    ...  # request or wait_for_task deadline exceeded
except AbregeAPIError as e:
    ...  # e.status_code / e.message - any other non-2xx response
```
