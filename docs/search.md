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
| `complete` | Finished successfully |
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
    if result.status in ("complete", "failed"):
        break
    time.sleep(10)

if result.status == "complete":
    print("Search finished:", result.id)
else:
    print("Search failed")
```

## Submit a DDA (Sage) search

```python
client.submit_search("exp_...", "proj_...", {
    "database": {
        "fasta": "fasta_...",          # database ID returned by upload_database
        "enzyme": {"missed_cleavages": 1},
        "static_mods": [{"residue": "C", "monoisotopic_mass": 57.021464}],
        "variable_mods": [{"residue": "M", "monoisotopic_mass": 15.994915}],
        "decoy_tag": "rev_",
    },
    "precursor_tol": {"ppm": [-20, 20]},
    "fragment_tol": {"ppm": [-20, 20]},
    "report_psms": 1,
})
```

## Submit a DIA search

```python
client.submit_search_dia("exp_...", "proj_...", {
    "database": {
        "spectral_lib": "spectral_lib_...",  # spectral library ID
        "params": {
            "smoothing": True,
            "min_points_per_peak": "3",
        },
    },
})
```

## Submit a PRM search

```python
client.submit_search_prm("exp_...", "proj_...", {
    "params": {
        "ms1_ppm_tolerance": 10,
        "ms2_ppm_tolerance": 10,
        "use_lib_retention_time": True,
    },
})
```
