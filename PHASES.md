# Chaparral Public API — Implementation Phases

Planning document for the programmatic API that lets existing Chaparral users
access the platform via Python (CLI, notebooks, CI pipelines, scripts) without
copy-pasting JWTs from DevTools.

---

## Architecture (final, simplified)

```
ch-frontend ──Authorization: Bearer <JWT>──────────► ch-backend  (existing)
                                                           ▲
Python SDK  ──Authorization: Bearer chpr_live_…───────────┘
                 (same server, new auth path in jwt.rs)
```

- **No new service.** `ch-backend` is already the API server. The Python SDK
  talks to it directly, exactly like `ch-frontend` does — just with an API key
  instead of a JWT.
- **No new infra.** No new ECS task, no new subdomain, no new DNS record.
- **One new DB table.** `api_keys` on the existing CockroachDB `defaultdb`.
  No existing table is altered.

## Auth model (clone of Anthropic / GitHub PATs)

- Keys issued from the web UI: **Settings → API Keys → Create Key**.
- Format: `chpr_live_<8-char-prefix>_<base32-secret>`.
- Server stores only `sha256(key)` — plaintext shown **once** at creation.
- Keys **never expire by default**; user revokes manually. Optional expiry date.
- Revocation is instant (`UPDATE api_keys SET revoked_at = now()`).
- On every request `ch-backend` looks up by prefix, constant-time compares hash,
  checks `revoked_at` / `expires_at`, assembles `Claims` identically to a JWT.

---

## Phases

### Phase 1 — Database schema ✅

Files: `ch-backend/migrations/20260506120000_add_api_keys.{up,down}.sql`

New table `api_keys`:

| Column | Type | Notes |
|---|---|---|
| `id` | `text PK` | `type_id("ak_")` |
| `organization_id` | `text FK → organizations` | |
| `user_id` | `text FK → users` | |
| `name` | `text` | user-given label |
| `prefix` | `text` | first segment, stored plaintext for UI display |
| `key_hash` | `bytes UNIQUE` | `sha256(full_token)` |
| `scopes` | `text[]` | default `["full_access"]` |
| `created_at` | `timestamptz` | |
| `last_used_at` | `timestamptz NULL` | async-updated on each request |
| `expires_at` | `timestamptz NULL` | optional user-set expiry |
| `revoked_at` | `timestamptz NULL` | set on revoke, NULL = active |

Two indexes: `idx_api_keys_user (user_id)`, `idx_api_keys_prefix (prefix)`.

Migration runs automatically at `ch-backend` deploy when `AUTO_MIGRATION=true`.
Rolled back with `DROP TABLE api_keys` — safe, nothing else references it.

### Phase 2 — `ch-backend` key management endpoints ✅

File: `ch-backend/src/api_keys.rs`

All three endpoints sit behind the existing JWT middleware (cookie/browser auth
required to issue or revoke). Used by the web UI's Settings page.

| Method | Path | Returns |
|---|---|---|
| `POST` | `/api-keys` | `{ id, name, prefix, key, scopes, created_at }` — `key` shown once |
| `GET` | `/api-keys` | list of keys for the calling user (no plaintext, no hash) |
| `DELETE` | `/api-keys/:id` | `204` — sets `revoked_at = now()` |

### Phase 3 — `ch-backend` accepts API-key bearer tokens ✅

File: `ch-backend/src/jwt.rs`

`authenticate_with_jwks` middleware branches on the bearer token prefix:
- Starts with `chpr_` → API-key path: look up in DB, constant-time hash compare,
  build `Claims`. Zero changes to any handler.
- Anything else → existing JWT decode path.

Result: **every existing `ch-backend` route now works with an API key** — no
per-route changes needed, ever.

### Phase 4 — Python SDK ✅

Repo: `chaparral-api/` (this repo).

Install:

```bash
pip install chaparral
```

Usage:

```python
from chaparral import Client

client = Client()  # reads CHAPARRAL_API_KEY from env

for project in client.list_projects():
    print(project.id, project.name)

result = client.get_search_result("srch_06EX...")
```

Key design decisions:

- `httpx` for HTTP (sync client; async wrapper is a future phase).
- `pydantic` v2 for typed, validated response models.
- `extra="allow"` on all models — SDK doesn't break when server adds fields.
- All SDK errors inherit from `ChaparralError`; `AuthenticationError`,
  `NotFoundError`, `RateLimitError` for specific cases.
- `py.typed` marker — fully typed for mypy / pyright.

Covered endpoints (v0.1):

| Area | Methods |
|---|---|
| Organization | `get_organization` |
| Projects | `list_projects`, `get_project`, `create_project`, `delete_project` |
| Databases (FASTA) | `list_databases`, `get_database` |
| Search results | `list_search_results`, `get_search_result` |
| API key admin | `list_api_keys`, `create_api_key`, `revoke_api_key` |

### Phase 5 — `ch-frontend` Settings → API Keys page (next)

New page in the Chaparral web UI. Required so users can issue and revoke keys
without DevTools.

UX flow (mirrors Anthropic console):

1. Settings → API Keys (new sidebar item).
2. Table: Name | Prefix | Created | Last used | Actions (Revoke).
3. "Create Key" button → modal: name input, optional expiry picker → Create.
4. One-time reveal modal: "Copy this key now — it won't be shown again."
   Copy-to-clipboard button. Confirm dismiss.
5. Revoke button → confirmation → `DELETE /api-keys/:id` → row updates to
   show "Revoked" with timestamp.

Implementation: new route `/settings/api-keys` in `ch-frontend`, calls the
`/api-keys` endpoints added in Phase 2.

### Phase 6 — Deploy ch-backend to testing ✅ (next deploy)

Normal `ch-backend` deploy to the testing environment:

- `AUTO_MIGRATION=true` → `api_keys` table created automatically.
- No other config changes needed.
- Verify: `psql` into testing cluster, confirm `api_keys` table exists.

### Phase 7 — End-to-end test on testing

1. Log into testing `ch-frontend` in browser.
2. Go to Settings → API Keys → Create Key; copy the `chpr_live_…` key.
3. Run a Python script using the SDK:
   ```bash
   CHAPARRAL_API_KEY="chpr_live_..." python -c "
   from chaparral import Client
   c = Client()
   print(c.list_projects())
   "
   ```
4. Verify `last_used_at` updates in the DB.
5. Click Revoke in the UI; confirm the next SDK call returns `401`.

### Phase 8 — Prod deploy

1. Normal `ch-backend` prod deploy — migration runs, table created.
2. Deploy `ch-frontend` with Settings → API Keys page.
3. Publish `pip install chaparral` to PyPI.
4. Announce to users.

### Phase 9 — User how-to documentation

Live in the `chaparral-api` repo under `docs/`. Written as standalone Markdown
pages (no build tool required — readable on GitHub directly).

Planned guides:

| File | Audience | Content |
|---|---|---|
| `docs/quickstart.md` | All users | Install, get an API key, first script in 5 min |
| `docs/authentication.md` | All users | Key format, env vars, `.env` file, key rotation, revocation |
| `docs/projects.md` | Bioinformatics users | List/create/delete projects; upload FASTA databases |
| `docs/search.md` | Bioinformatics users | Submit a search, poll status, download results |
| `docs/error_handling.md` | Developers | Exception hierarchy, retry strategy, debugging tips |
| `docs/examples/` | All users | Runnable `.py` scripts: batch search, result export, CI pipeline |

Each guide follows the same structure:
1. **Goal** — one-sentence description of what the user will accomplish.
2. **Prerequisites** — SDK installed, API key set.
3. **Step-by-step** — minimal working code with inline comments.
4. **Reference** — links to relevant `Client` methods.

---

## Repository layout (current)

```
chaparral-api/                  ← this repo (Python SDK only)
├── pyproject.toml
├── README.md
├── PHASES.md
├── .env.example
├── docs/
│   ├── quickstart.md
│   ├── authentication.md
│   ├── projects.md
│   ├── search.md
│   ├── error_handling.md
│   └── examples/
│       ├── batch_search.py
│       ├── export_results.py
│       └── ci_pipeline.py
├── src/chaparral/
│   ├── __init__.py             ← public surface
│   ├── client.py               ← Client class
│   ├── models.py               ← pydantic models
│   ├── exceptions.py           ← error hierarchy
│   └── py.typed                ← PEP 561 marker
└── tests/
    └── test_client.py          ← mocked unit tests (pytest-httpx)
```

---

## What remains (priority order)

- [ ] Phase 5: `ch-frontend` Settings → API Keys page.
- [ ] Phase 6: deploy `ch-backend` to testing (next normal deploy).
- [ ] Phase 7: end-to-end test.
- [ ] Phase 8: prod deploy + PyPI publish.
- [ ] Phase 9: user how-to docs (`docs/quickstart.md`, `docs/authentication.md`, `docs/projects.md`, `docs/search.md`, `docs/error_handling.md`, `docs/examples/`).
- [ ] SDK: expand endpoint coverage (experiments, search submit, file upload, QC, results download).
- [ ] SDK: async client wrapper (`AsyncClient`).
- [ ] SDK: auto-retry with exponential backoff on `429`.
- [ ] SDK: pagination helpers for large result sets.
