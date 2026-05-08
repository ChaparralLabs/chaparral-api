# Authentication

## API key format

Keys are issued per-user and look like:

```
chpr_live_A1B2C3D4_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

- `chpr_live_` — fixed prefix identifying Chaparral live keys.
- `A1B2C3D4` — 8-character display prefix (visible in the UI after creation).
- The remainder — 24-byte secret, shown **only once** at creation.

The server stores only a SHA-256 hash of your key. If you lose it, revoke it
and create a new one.

## Setting your key

### Environment variable (recommended)

```bash
export CHAPARRAL_API_KEY="chpr_live_..."
```

The `Client` reads this automatically:

```python
from chaparral import Client

client = Client()  # uses CHAPARRAL_API_KEY
```

### `.env` file

Create a `.env` file in your project root (never commit it):

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

Add `.env` to `.gitignore`:

```
.env
```

### Explicit argument

```python
client = Client(api_key="chpr_live_...")
```

Use this for tests or multi-tenant scripts where each user has their own key.

## Multiple environments

```python
import os
from chaparral import Client

client = Client(
    api_key=os.environ["CHAPARRAL_API_KEY"],
    base_url=os.environ.get("CHAPARRAL_BASE_URL", "https://api.chaparral.ai"),
)
```

Set `CHAPARRAL_BASE_URL` to point at a testing environment:

```bash
export CHAPARRAL_BASE_URL="https://testing.chaparral.ai"
```

## Key rotation

1. Create a new key in **Settings → API Keys**.
2. Update `CHAPARRAL_API_KEY` in your environment / secrets manager.
3. Revoke the old key in **Settings → API Keys → Revoke**.

Old key stops working the moment it is revoked — no grace period.

## Revoking a key

### Via the web UI

Settings → API Keys → click **Revoke** next to the key.

### Via the SDK

```python
from chaparral import Client

client = Client()

keys = client.list_api_keys()
for key in keys:
    if key.name == "old-ci-key":
        client.revoke_api_key(key.id)
        print(f"Revoked {key.prefix}")
```

---

## Programmatic key management

These methods are useful for automated key rotation or provisioning keys in CI.

### `list_api_keys() → List[ApiKey]`

List all API keys belonging to your user (active and revoked).

```python
for key in client.list_api_keys():
    status = "revoked" if key.revoked_at else "active"
    last_used = key.last_used_at.date() if key.last_used_at else "never"
    print(f"{key.prefix}  {key.name:<20}  {status:<8}  last used: {last_used}")
```

### `create_api_key(*, name, scopes=None, expires_at=None) → CreatedApiKey`

Create a new API key. The plaintext key is returned **only once** — store it immediately.

```python
created = client.create_api_key(name="ci-nightly")
print(created.key)   # chpr_live_XXXXXXXX_... — save this now

# With expiry (ISO 8601 string)
created = client.create_api_key(name="temp-key", expires_at="2026-12-31T00:00:00Z")
```

### `revoke_api_key(api_key_id) → None`

Revoke a key by ID. Effective immediately.

```python
for key in client.list_api_keys():
    if key.name == "old-laptop":
        client.revoke_api_key(key.id)
        print(f"Revoked {key.prefix}")
```

**`ApiKey` fields:**

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Key ID (use for revocation) |
| `name` | `str` | Human-readable label |
| `prefix` | `str` | 8-char display prefix, visible in logs |
| `scopes` | `List[str]` | e.g. `["full_access"]` |
| `created_at` | `datetime` | Creation timestamp |
| `last_used_at` | `datetime \| None` | Last successful auth |
| `expires_at` | `datetime \| None` | Expiry, or `None` if no expiry |
| `revoked_at` | `datetime \| None` | Revocation time, or `None` if active |

`CreatedApiKey` has all `ApiKey` fields plus `key: str` — the full plaintext key, shown only at creation.

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
