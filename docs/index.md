# Chaparral Python SDK

Official Python client for the [Chaparral](https://chaparral.ai) proteomics
mass-spectrometry platform.

## Guides

| Guide | Description |
|---|---|
| [Quickstart](quickstart.md) | Install, get an API key, run your first script |
| [Authentication](authentication.md) | Key management, rotation, environments, programmatic key admin |
| [Projects & Databases](projects.md) | Manage projects, FASTA databases, and your organization |
| [Experiments & Uploads](experiments.md) | Create experiments, upload raw files and mzparquet |
| [Search Results](search.md) | Submit DDA/DIA/PRM searches, poll status |
| [Error Handling](error_handling.md) | Exception hierarchy, retries, debugging |

## Examples

Runnable scripts in [examples/](examples/):

| File | Description |
|---|---|
| [batch_search.py](examples/batch_search.py) | Poll multiple searches until all complete |
| [ci_pipeline.py](examples/ci_pipeline.py) | Verify projects and searches in CI |
| [export_results.py](examples/export_results.py) | Export completed searches to CSV |
