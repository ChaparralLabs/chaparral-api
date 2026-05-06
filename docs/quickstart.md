# Quickstart

Get from zero to your first API call in 5 minutes.

## Prerequisites

- Python 3.9+
- A Chaparral account at [app.chaparral.ai](https://app.chaparral.ai)

## 1. Install the SDK

```bash
pip install chaparral
```

## 2. Get an API key

1. Log into [app.chaparral.ai](https://app.chaparral.ai).
2. Go to **Settings → API Keys**.
3. Click **Create Key**, give it a name, click **Create**.
4. Copy the key — it starts with `chpr_live_` and is shown **only once**.

## 3. Set the environment variable

```bash
export CHAPARRAL_API_KEY="chpr_live_..."
```

Or store it in a `.env` file (see [authentication.md](authentication.md)).

## 4. Run your first script

```python
from chaparral import Client

client = Client()

# List your projects
for project in client.list_projects():
    print(project.id, project.name)
```

## 5. Fetch a search result

```python
from chaparral import Client

client = Client()

result = client.get_search_result("srch_...")
print(result.id, result.status)
```

## Next steps

- [Authentication](authentication.md) — key rotation, `.env` files, multiple environments.
- [Projects](projects.md) — create projects, upload FASTA databases.
- [Search](search.md) — submit searches, poll status, download results.
- [Error handling](error_handling.md) — handle errors and retries gracefully.
