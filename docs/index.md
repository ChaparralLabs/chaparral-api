# Chaparral Python SDK

Official Python client for the [Chaparral](https://chaparral.ai) proteomics
mass-spectrometry platform.

## Guides

| Guide | Description |
|---|---|
| [Quickstart](quickstart.md) | Install, get an API key, run your first script |
| [Authentication](authentication.md) | Key management, rotation, environments, programmatic key admin |
| [Projects & Databases](projects.md) | Manage projects, FASTA databases, and your organization |
| [Search Results](search.md) | Poll searches and check status |
| [Error Handling](error_handling.md) | Exception hierarchy, retries, debugging |

## Examples

Runnable scripts in [examples/](examples/):

| File | Description |
|---|---|
| [batch_search.py](examples/batch_search.py) | Poll multiple searches until all complete |
| [ci_pipeline.py](examples/ci_pipeline.py) | Verify projects and searches in CI |
| [export_results.py](examples/export_results.py) | Export completed searches to CSV |
