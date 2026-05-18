# Contributing

## Development setup

```bash
git clone https://github.com/ChaparralLabs/chaparral-api
cd chaparral-api
pip install -e ".[dev]"
pytest
```

## SDK design

- **`httpx`** for HTTP — synchronous client; async wrapper is a future phase.
- **`pydantic` v2** for typed, validated response models.
- **`extra="allow"`** on all models — the SDK does not break when the server adds new fields. Undocumented fields are accessible via `model.model_extra`.
- All SDK errors inherit from `ChaparralError`; `AuthenticationError`, `NotFoundError`, `RateLimitError` for specific HTTP status codes.
- **`py.typed`** marker — fully typed for mypy / pyright.

## Covered endpoints (v0.1)

| Area | Methods |
|---|---|
| Organization | `get_organization` |
| Projects | `list_projects`, `get_project`, `create_project`, `delete_project` |
| Databases (FASTA) | `list_databases`, `get_database` |
| Search results | `list_search_results`, `get_search_result` |
| API key admin | `list_api_keys`, `create_api_key`, `revoke_api_key` |

More endpoints (experiments, search submission, file uploads, QC, results file downloads) are planned for subsequent releases.

## Running tests

```bash
pytest
```

Tests use `pytest-httpx` to mock HTTP responses — no real API calls are made.

## Type checking

```bash
mypy src/
```

## Linting

```bash
ruff check src/ tests/
```
