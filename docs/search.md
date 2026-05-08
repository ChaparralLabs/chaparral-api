# Search Results

## List all search results

```python
from chaparral import Client

client = Client()

results = client.list_search_results()
for r in results:
    print(r.id, r.status)
```

## Get a specific result

```python
result = client.get_search_result("srch_...")
print(result.id, result.status, result.created_at)
```

The `status` field reflects the processing state of the search:

| Status | Meaning |
|---|---|
| `pending` | Queued, not yet started |
| `running` | Currently processing |
| `completed` | Finished successfully |
| `failed` | Processing error |

## Poll until complete

```python
import time
from chaparral import Client

client = Client()

result_id = "srch_..."
while True:
    result = client.get_search_result(result_id)
    print(f"Status: {result.status}")
    if result.status in ("completed", "failed"):
        break
    time.sleep(10)

if result.status == "completed":
    print("Search finished:", result.id)
else:
    print("Search failed")
```

> **Note**: Search submission (uploading raw files and triggering a new search)
> is not yet available in the SDK (v0.1). Submit searches via the web UI at
> [app.chaparral.ai](https://app.chaparral.ai). Programmatic submission will be
> added in a future release.
