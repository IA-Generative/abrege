# abrege-sdk

Python client for the Abrège API, sync (`SyncAbregeClient`) and async (`AsyncAbregeClient`).

## Authentication

Two ways to authenticate:

**Static API key** (e.g. a Keycloak service-account token):

```python
from abrege_sdk.client_sync import SyncAbregeClient

with SyncAbregeClient("http://localhost:5000", api_key="...") as client:
    task = client.summarize_text(...)
```

**Username/password** (real user identity, via Keycloak Resource Owner Password
Credentials grant - the Keycloak client secret never leaves the backend):

```python
with SyncAbregeClient("http://localhost:5000") as client:
    client.login("user@example.com", "hunter2")
    task = client.summarize_text(...)
```

The async client (`AsyncAbregeClient`) mirrors the same API with `async`/`await`.

## Tasks

```python
task = client.summarize_doc("report.pdf")
task = client.get_task(task.id)
text = client.get_task_text(task.id)          # convenience over task.output.summary
page = client.get_user_tasks(page=1, page_size=10)
client.cancel_task(task.id)
client.delete_task(task.id)
```
