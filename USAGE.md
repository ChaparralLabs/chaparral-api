# Chaparral Python SDK — Usage Guide

## What are API keys and why do you need one?

API keys are the credential that lets external code (scripts, pipelines,
notebooks, CI systems) talk to Chaparral on your behalf — without requiring
your password or a browser session.

**Common use cases for customers:**

| Scenario | Why an API key |
|---|---|
| Automated pipeline (Nextflow, Snakemake, batch scripts) | Submit searches and poll results unattended, overnight or on a cluster |
| Jupyter / R notebooks | Pull search results and FASTA databases directly into analysis without copy-pasting files |
| CI/CD (GitHub Actions, GitLab CI) | Regression tests that run a real search and assert expected PSM counts |
| Shared lab server | One key per project or person — revoke individually if someone leaves, no password reset needed |
| Third-party integrations | Vendor tools or LIMS systems that push data into Chaparral |

Keys are scoped to your user account and carry `full_access` by default. You
can create multiple keys with different names to track which system is making
which requests (the prefix `ADQ87WT2` appears in server logs and in the UI).

---

## Installation

```bash
pip install chaparral
```

Requires Python 3.9+. The only runtime dependencies are `httpx` and `pydantic`.

---

## Getting an API key

1. Log into [app.chaparral.ai](https://app.chaparral.ai).
2. Go to **Settings → API Keys**.
3. Click **Create Key**.
4. Give the key a descriptive name — e.g. `laptop`, `lab-server`, `github-actions`.
5. Click **Create**. Copy the key immediately — **it is shown only once**.

Keys look like:

```
chpr_live_ADQ87WT2_9HYNPM7FKJH7ZMTD6B8F2D8JKK1PRKWXQA20PPR
          ^^^^^^^^ — display prefix (visible in UI & logs)
```

The server stores only a hash of the secret portion. If you lose the key,
revoke it and create a new one.

---

## Setting the key

### Option A — Environment variable (recommended)

```bash
# macOS / Linux
export CHAPARRAL_API_KEY="chpr_live_..."

# Windows PowerShell
$env:CHAPARRAL_API_KEY = "chpr_live_..."
```

The `Client` reads this automatically:

```python
from chaparral import Client

client = Client()   # picks up CHAPARRAL_API_KEY
```

### Option B — `.env` file

Create `.env` in your project root (**never commit this file**):

```
CHAPARRAL_API_KEY=chpr_live_...
```

Load it with [python-dotenv](https://pypi.org/project/python-dotenv/):

```python
from dotenv import load_dotenv
from chaparral import Client

load_dotenv()
client = Client()
```

Add to `.gitignore`:

```
.env
```

### Option C — Explicit argument

Fine for short scripts; avoid hard-coding in files that get committed.

```python
client = Client(api_key="chpr_live_...")
```

---

## Quick start

```python
from chaparral import Client

client = Client()   # reads CHAPARRAL_API_KEY

# List your projects
for project in client.list_projects():
    print(project.id, project.name)

# Fetch a specific search result
result = client.get_search_result("srch_06EX...")
print(result.status, result.program)
```

---

## Common operations

### List projects

```python
projects = client.list_projects()
for p in projects:
    print(p.id, p.name, p.description)
```

### Create a project

```python
project = client.create_project(name="My Experiment", description="TMT 16-plex")
print(project.id)
```

### List FASTA databases

```python
for db in client.list_databases():
    print(db.id, db.name)
```

### Fetch a search result

```python
result = client.get_search_result("srch_...")
print(result.id, result.status)   # pending | running | completed | failed
```

### Manage API keys programmatically

```python
# List your keys
for key in client.list_api_keys():
    print(key.prefix, key.name, "revoked" if key.revoked_at else "active")

# Create a new key (useful in automation)
created = client.create_api_key(name="ci-nightly")
print(created.key)   # save this — shown only once

# Revoke a key by ID
client.revoke_api_key("ak_06F09...")
```

---

## Context manager

The client holds an HTTP connection pool. For scripts, use a `with` block to
close it cleanly:

```python
from chaparral import Client

with Client() as client:
    projects = client.list_projects()
```

---

## Error handling

```python
from chaparral import Client, AuthenticationError, NotFoundError, RateLimitError, ApiError

client = Client()

try:
    result = client.get_search_result("srch_missing")
except AuthenticationError:
    print("Bad or revoked API key")
except NotFoundError:
    print("That search result doesn't exist")
except RateLimitError:
    print("Too many requests — back off and retry")
except ApiError as exc:
    print(f"API error {exc.status_code}: {exc}")
```

---

## Configuration reference

| Constructor arg | Environment variable   | Default                        |
|-----------------|------------------------|--------------------------------|
| `api_key`       | `CHAPARRAL_API_KEY`    | required                       |
| `base_url`      | `CHAPARRAL_BASE_URL`   | `https://api.chaparral.ai`     |
| `timeout`       | —                      | `30.0` seconds                 |

---

## Revoking a key

From the UI: **Settings → API Keys → Revoke** next to the key.  
From code:

```python
client.revoke_api_key("ak_06F09...")
```

Revocation is immediate. Any in-flight requests using that key will fail with
`401 Unauthorized`.

---

## Security best practices

- Treat API keys like passwords — never put them in source code or commit them to git.
- Use one key per environment or service so you can revoke individually.
- Rotate keys periodically or whenever a team member leaves.
- In CI/CD, store the key in your secrets manager (GitHub Secrets, AWS Secrets Manager, etc.).
