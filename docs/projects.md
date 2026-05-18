# Projects, Databases & Organization

## Organization

Each API key belongs to a single organization. Use `get_organization` to retrieve
your organization's ID and name.

```python
from chaparral import Client

client = Client()

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

## Projects

A project groups a set of searches together. Each project belongs to your
organization.

### List projects

```python
from chaparral import Client

client = Client()

projects = client.list_projects()
for p in projects:
    print(p.id, p.name)
```

### Get a specific project

```python
project = client.get_project("proj_...")
print(project.name, project.created_at)
```

### Create a project

```python
project = client.create_project(name="My experiment", description="DDA run May 2026")
print(project.id)
```

### Delete a project

```python
client.delete_project("proj_...")
```

Deletion is permanent. All searches associated with the project are also
removed.

---

## Databases (FASTA)

A database is a FASTA protein sequence file uploaded to Chaparral. Databases
are shared across projects within your organization.

### List databases

```python
databases = client.list_databases()
for db in databases:
    print(db.id, db.name)
```

### Get a specific database

```python
db = client.get_database("db_...")
print(db.name, db.created_at)
```

> **Note**: To upload a FASTA file programmatically use `client.upload_database("/path/to/file.fasta")`.
> See [Experiments & Uploads](experiments.md) for details.
