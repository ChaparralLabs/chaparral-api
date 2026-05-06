# chaparral

Official Python client for the [Chaparral](https://chaparral.ai) proteomics
mass-spectrometry platform.

```bash
pip install chaparral
```

## Quick start

```python
from chaparral import Client

# Reads CHAPARRAL_API_KEY from the environment by default.
client = Client()

for project in client.list_projects():
    print(project.id, project.name)

result = client.get_search_result("srch_06EX...")
print(result.status, result.program)
```

## Getting an API key

1. Log into [chaparral.ai](https://chaparral.ai) in your browser.
2. Go to **Settings → API Keys → Create Key**.
3. Give the key a name (e.g. `laptop`, `ci-prod`) and click **Create**.
4. Copy the key shown in the modal — **it will not be displayed again**.
5. Use it in your scripts:

   ```bash
   export CHAPARRAL_API_KEY="chpr_live_XXXXXXXX_..."
   ```

   Or pass it explicitly:

   ```python
   client = Client(api_key="chpr_live_...")
   ```

Keys never expire by default. Revoke any key any time from the same Settings
page; revocation takes effect immediately.

## Configuration

| Argument          | Env var                | Default                       |
|-------------------|------------------------|-------------------------------|
| `api_key`         | `CHAPARRAL_API_KEY`    | (required)                    |
| `base_url`        | `CHAPARRAL_BASE_URL`   | `https://api.chaparral.ai`    |
| `timeout`         | —                      | `30.0` seconds                |

## Coverage (v0.1)

| Area              | Endpoints |
|-------------------|-----------|
| Organization      | `get_organization` |
| Projects          | `list_projects`, `get_project`, `create_project`, `delete_project` |
| Databases (FASTA) | `list_databases`, `get_database` |
| Search results    | `list_search_results`, `get_search_result` |
| API key admin     | `list_api_keys`, `create_api_key`, `revoke_api_key` |

More endpoints (experiments, search submission, file uploads, QC, results
file downloads) will be added in subsequent releases.

## Errors

All exceptions inherit from `ChaparralError`:

```python
from chaparral import ChaparralError, NotFoundError, RateLimitError

try:
    client.get_project("missing")
except NotFoundError:
    ...
except RateLimitError as exc:
    print("Backoff and retry:", exc)
except ChaparralError as exc:
    print("Generic failure:", exc)
```

## Development

```bash
git clone https://github.com/chaparral-ai/chaparral-api
cd chaparral-api
pip install -e ".[dev]"
pytest
```
