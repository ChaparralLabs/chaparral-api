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
4. Give the key a descriptive name
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

for project in client.list_projects():
    print(project.id, project.name)
```

---

## Full API reference

### `Client(api_key, *, base_url, timeout, user_agent)`

Creates a client instance. All parameters except `api_key` are optional.

```python
from chaparral import Client

# From environment variable (recommended)
client = Client()

# Explicit key
client = Client(api_key="chpr_live_...")

# Override base URL (e.g. for testing environment)
client = Client(base_url="https://api.testing.chaparral.ai")

# Custom timeout in seconds (default: 30)
client = Client(timeout=60)
```

Use as a context manager to close the connection pool cleanly:

```python
with Client() as client:
    projects = client.list_projects()
```

---

### Organization

#### `get_organization() → Organization`

Returns the organization the API key belongs to.

```python
org = client.get_organization()
print(org.id, org.name, org.created_at)
```

**Returns:** `Organization`

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Organization ID |
| `name` | `str` | Organization name |
| `created_at` | `datetime \| None` | Creation timestamp |

---

### Projects

#### `list_projects() → List[Project]`

List all projects visible to the caller.

```python
projects = client.list_projects()
for p in projects:
    print(p.id, p.name, p.description, p.tags)
```

#### `get_project(project_id) → Project`

Fetch a single project by ID.

```python
project = client.get_project("proj_06EVWN2PS...")
print(project.name, project.created_at)
```

#### `create_project(*, name, description="") → Project`

Create a new project.

```python
project = client.create_project(name="TMT 16-plex Run 1", description="May 2026 batch")
print(project.id)
```

#### `delete_project(project_id) → None`

Delete a project permanently.

```python
client.delete_project("proj_06EVWN2PS...")
```

**Returns:** `Project`

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Project ID |
| `name` | `str` | Project name |
| `description` | `str \| None` | Optional description |
| `organization_id` | `str \| None` | Owning org ID |
| `tags` | `List[str]` | User-defined tags |
| `created_at` | `datetime \| None` | Creation timestamp |

---

### Databases (FASTA)

#### `list_databases() → List[Database]`

List all FASTA proteome databases registered with your organization.

```python
for db in client.list_databases():
    print(db.id, db.name, db.organism)
```

#### `get_database(database_id) → Database`

Fetch a single database by ID.

```python
db = client.get_database("fasta_...")
print(db.name, db.decoy_tag)
```

**Returns:** `Database`

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Database ID |
| `name` | `str` | Display name |
| `organism` | `str \| None` | e.g. `"Homo sapiens"` |
| `decoy_tag` | `str \| None` | Decoy prefix, e.g. `"rev_"` |
| `organization_id` | `str \| None` | Owning org ID |
| `created_at` | `datetime \| None` | Creation timestamp |

---

### Search Results

#### `list_search_results() → List[SearchResult]`

List all search results visible to the caller.

```python
results = client.list_search_results()
for r in results:
    print(r.id, r.status, r.program)
```

#### `get_search_result(search_result_id) → SearchResult`

Fetch a single search result by ID. Poll this to check job completion.

```python
import time

result = client.get_search_result("srch_...")
while result.status not in ("completed", "failed"):
    time.sleep(10)
    result = client.get_search_result(result.id)

print(result.status)
```

**Returns:** `SearchResult`

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Search result ID |
| `name` | `str \| None` | Display name |
| `project_id` | `str \| None` | Parent project ID |
| `experiment_id` | `str \| None` | Parent experiment ID |
| `status` | `str \| None` | `pending` \| `running` \| `completed` \| `failed` |
| `program` | `str \| None` | Search engine used (e.g. `"sage"`) |
| `created_at` | `datetime \| None` | Creation timestamp |

---

### API Keys

These methods let you manage API keys programmatically — useful for automated key rotation or provisioning keys in CI.

#### `list_api_keys() → List[ApiKey]`

List all API keys belonging to your user (active and revoked).

```python
for key in client.list_api_keys():
    status = "revoked" if key.revoked_at else "active"
    last_used = key.last_used_at.date() if key.last_used_at else "never"
    print(f"{key.prefix}  {key.name:<20}  {status:<8}  last used: {last_used}")
```

#### `create_api_key(*, name, scopes=None, expires_at=None) → CreatedApiKey`

Create a new API key. The plaintext key is returned **only once** — store it immediately.

```python
created = client.create_api_key(name="ci-nightly")
print(created.key)   # chpr_live_XXXXXXXX_... — save this now

# With expiry (ISO 8601 string)
created = client.create_api_key(name="temp-key", expires_at="2026-12-31T00:00:00Z")
```

#### `revoke_api_key(api_key_id) → None`

Revoke a key by ID. Effective immediately — any requests using that key will start failing with `401`.

```python
# Revoke by ID from list_api_keys()
for key in client.list_api_keys():
    if key.name == "old-laptop":
        client.revoke_api_key(key.id)
        print(f"Revoked {key.prefix}")
```

**`ApiKey` fields:**

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Key ID (use this for revocation) |
| `name` | `str` | Human-readable label |
| `prefix` | `str` | 8-char display prefix, visible in logs |
| `scopes` | `List[str]` | e.g. `["full_access"]` |
| `created_at` | `datetime` | Creation timestamp |
| `last_used_at` | `datetime \| None` | Last successful auth |
| `expires_at` | `datetime \| None` | Expiry, or `None` if no expiry |
| `revoked_at` | `datetime \| None` | Revocation time, or `None` if active |

**`CreatedApiKey`** — same as `ApiKey` plus:

| Field | Type | Description |
|---|---|---|
| `key` | `str` | Full plaintext key — shown only at creation |

---

## Error handling

All exceptions inherit from `ChaparralError`:

```python
from chaparral import (
    Client,
    ChaparralError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ApiError,
)

client = Client()

try:
    result = client.get_search_result("srch_missing")
except AuthenticationError:
    # 401 — key is invalid, revoked, or expired
    print("Bad or revoked API key")
except NotFoundError:
    # 404 — resource doesn't exist or you don't have access
    print("Not found")
except RateLimitError:
    # 429 — slow down
    import time
    time.sleep(60)
except ApiError as exc:
    # Any other non-2xx response
    print(f"API error {exc.status_code}: {exc}")
    print(exc.body)   # raw response body
except ChaparralError as exc:
    # Network / transport errors (exc.status_code == 0)
    print(f"Connection error: {exc}")
```

---

## Configuration reference

| Constructor arg | Environment variable | Default |
|---|---|---|
| `api_key` | `CHAPARRAL_API_KEY` | required |
| `base_url` | `CHAPARRAL_BASE_URL` | `https://api.chaparral.ai` |
| `timeout` | — | `30.0` seconds |

---

## Security best practices

- Treat API keys like passwords — never put them in source code or commit them to git.
- Use one key per environment or service so you can revoke individually.
- Rotate keys periodically or whenever a team member leaves.
- In CI/CD, store the key in your secrets manager (GitHub Secrets, AWS Secrets Manager, etc.).
