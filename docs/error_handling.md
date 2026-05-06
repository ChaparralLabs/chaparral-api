# Error Handling

## Exception hierarchy

All SDK errors inherit from `ChaparralError`:

```
ChaparralError
└── ApiError                    # HTTP error from the server
    ├── AuthenticationError     # 401 — invalid or revoked key
    ├── NotFoundError           # 404 — resource does not exist
    └── RateLimitError          # 429 — too many requests
```

## Basic pattern

```python
from chaparral import Client
from chaparral.exceptions import AuthenticationError, NotFoundError, ApiError

client = Client()

try:
    project = client.get_project("proj_does_not_exist")
except NotFoundError:
    print("Project not found")
except AuthenticationError:
    print("Check your CHAPARRAL_API_KEY")
except ApiError as e:
    print(f"Server error {e.status_code}: {e.message}")
```

## Handling a revoked key

```python
from chaparral.exceptions import AuthenticationError

try:
    results = client.list_search_results()
except AuthenticationError:
    # Key was revoked or never valid — prompt user to re-issue
    raise SystemExit("API key invalid. Create a new one at app.chaparral.ai → Settings → API Keys.")
```

## Rate limiting

The server returns `429` when too many requests are sent in a short window.
Handle it with exponential backoff:

```python
import time
from chaparral.exceptions import RateLimitError

def list_with_retry(client, retries=5):
    delay = 1.0
    for attempt in range(retries):
        try:
            return client.list_search_results()
        except RateLimitError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)
            delay *= 2
    return []
```

> Automatic retry with backoff will be built into the client in a future release.

## Inspecting errors

`ApiError` exposes three attributes:

```python
except ApiError as e:
    print(e.status_code)   # int, e.g. 422
    print(e.message)       # str from server JSON {"message": "..."}
    print(e.body)          # raw parsed JSON body (dict | list | None)
```

## Debugging

Set the `CHAPARRAL_BASE_URL` env var to point at a testing environment where
you can inspect server logs:

```bash
CHAPARRAL_BASE_URL="https://testing.chaparral.ai" python your_script.py
```

Enable `httpx` request/response logging for low-level inspection:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
# httpx will log request headers and response bodies
```
