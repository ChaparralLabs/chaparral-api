# Experiments & File Uploads

An experiment groups a set of raw MS files together within a project.
Searches are run against the files in an experiment.

## List experiments

```python
from chaparral import Client

client = Client()

# All experiments across your organization
experiments = client.list_experiments()
for exp in experiments:
    print(exp.id, exp.name, exp.storage_status)

# Experiments in a specific project
experiments = client.list_experiments_by_project("proj_...")
```

## Get a specific experiment

```python
exp = client.get_experiment("exp_...", "proj_...")
print(exp.name, exp.created_at, exp.storage_bytes)
```

## Create an experiment

```python
exp = client.create_experiment(
    name="DDA run May 2026",
    description="Tryptic digest, LFQ",
    project_id="proj_...",
    tags=["dda", "lfq"],
)
print(exp.id)
```

## Delete an experiment

```python
client.delete_experiment("exp_...", "proj_...")
```

Deletion is permanent. All raw files and search results in the experiment
are also removed.

---

## Raw file upload

Upload raw MS files directly to an experiment. Supported formats:

| Format | Description |
|---|---|
| `.raw` | Thermo Fisher RAW file — automatically converted to mzparquet |
| `.mzML` | Open mzML format — automatically converted to mzparquet |
| `.d` (Bruker) | Upload both `.tdf` and `.tdf_bin` — automatically converted |
| `.mzparquet` | Pre-converted file — use `upload_mzparquet` |

### Upload a raw file

```python
client.upload_raw_file("exp_...", "proj_...", "/path/to/sample.raw")
```

The backend streams the file to S3 and triggers mzparquet conversion automatically.

### Upload a pre-converted mzparquet

```python
client.upload_mzparquet("exp_...", "proj_...", "/path/to/sample.mzparquet")
```

### Upload multiple files

```python
import pathlib

raw_dir = pathlib.Path("/data/runs/may2026")
for f in raw_dir.glob("*.raw"):
    print(f"Uploading {f.name}...")
    client.upload_raw_file("exp_...", "proj_...", f)
print("Done.")
```

### List uploaded files

```python
files = client.list_raw_files("exp_...", "proj_...")
for f in files:
    print(f.file, f.extension, f.job_status, f.storage_status)
```

`job_status` reflects the mzparquet conversion job (e.g. `RUNNING`, `SUCCEEDED`).
`storage_status` is `active` for files available for searching, `archived` for
cold-stored files.

---

## Upload a FASTA database

```python
databases = client.upload_database("/path/to/human.fasta")
for db in databases:
    print(db.id, db.name)
```

The returned `id` is used as the `database.fasta` field when submitting a search.
See [Search Results](search.md) for full search submission examples.
