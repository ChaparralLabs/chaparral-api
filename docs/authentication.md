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
