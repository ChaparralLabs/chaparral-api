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

## Documentation

- [Quickstart](docs/quickstart.md) — installation, API key, first script.
- [Authentication](docs/authentication.md) — key rotation, `.env` files, multiple environments, programmatic key management.
- [Projects & Databases](docs/projects.md) — manage projects, FASTA databases, and your organization.
- [Search Results](docs/search.md) — poll searches and check status.
- [Error Handling](docs/error_handling.md) — exception hierarchy, retries, debugging.
- [Examples](docs/examples/) — runnable scripts for common tasks.

## Development

```bash
git clone https://github.com/chaparral-ai/chaparral-api
cd chaparral-api
pip install -e ".[dev]"
pytest
```
