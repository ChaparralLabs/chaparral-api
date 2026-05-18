"""Synchronous Chaparral API client.

The client is a thin, typed wrapper around ``ch-backend``'s REST endpoints.
Authentication uses a long-lived API key (``Authorization: Bearer chpr_...``)
that the user issues from the Chaparral web UI under Settings → API Keys.
"""

from __future__ import annotations

import os
import pathlib
import time
from typing import Any, Iterable, List, Mapping, Optional, Union

import httpx

from chaparral.exceptions import (
    ApiError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)
from chaparral.models import (
    ApiKey,
    CreatedApiKey,
    Database,
    Experiment,
    Json,
    OrgUsage,
    Organization,
    Project,
    RawFile,
    SearchResult,
    SpectralLib,
)

DEFAULT_BASE_URL = "https://api.chaparral.ai"
DEFAULT_TIMEOUT = 30.0


class Client:
    """Synchronous Chaparral client.

    Parameters
    ----------
    api_key:
        Bearer token of the form ``chpr_live_<prefix>_<secret>``. If omitted,
        the value of the ``CHAPARRAL_API_KEY`` environment variable is used.
    base_url:
        Override the API endpoint. Defaults to ``CHAPARRAL_BASE_URL`` env var
        or ``https://api.chaparral.ai``.
    timeout:
        Per-request timeout in seconds.
    user_agent:
        Custom User-Agent header. Useful for telemetry on the server side.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = "chaparral-python/0.3.0",
    ) -> None:
        key = api_key or os.environ.get("CHAPARRAL_API_KEY")
        if not key:
            raise AuthenticationError(
                "No API key provided. Pass api_key= or set CHAPARRAL_API_KEY.",
                status_code=401,
            )
        url = base_url or os.environ.get("CHAPARRAL_BASE_URL", DEFAULT_BASE_URL)

        self._http = httpx.Client(
            base_url=url.rstrip("/"),
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {key}",
                "User-Agent": user_agent,
                "Accept": "application/json",
            },
        )

    # ------------------------------------------------------------------ lifecycle
    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # ------------------------------------------------------------------- helpers
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[Any] = None,
        content: Optional[bytes] = None,
        headers: Optional[Mapping[str, str]] = None,
        files: Optional[Any] = None,
    ) -> httpx.Response:
        try:
            resp = self._http.request(
                method,
                path,
                params=params,
                json=json,
                content=content,
                headers=headers,
                files=files,
            )
        except httpx.HTTPError as exc:  # network / transport errors
            raise ApiError(str(exc), status_code=0) from exc

        if resp.is_success:
            return resp

        body: Any
        try:
            body = resp.json()
        except ValueError:
            body = resp.text

        message = (body.get("message") if isinstance(body, dict) else None) or resp.text or resp.reason_phrase
        if resp.status_code == 401:
            raise AuthenticationError(message, status_code=401, body=body)
        if resp.status_code == 404:
            raise NotFoundError(message, status_code=404, body=body)
        if resp.status_code == 429:
            raise RateLimitError(message, status_code=429, body=body)
        raise ApiError(message, status_code=resp.status_code, body=body)

    def _get_json(self, path: str, **params: Any) -> Json:
        return self._request("GET", path, params=params or None).json()

    # -------------------------------------------------------------- organization
    def get_organization(self) -> Organization:
        """Return the organization the API key belongs to."""
        return Organization.model_validate(self._get_json("/users/organization"))

    # ----------------------------------------------------------------- projects
    def list_projects(self) -> List[Project]:
        """List all projects visible to the caller."""
        data = self._get_json("/projects")
        return [Project.model_validate(p) for p in data]

    def get_project(self, project_id: str) -> Project:
        """Fetch a single project by ID."""
        return Project.model_validate(self._get_json(f"/projects/{project_id}"))

    def create_project(self, *, name: str, description: str = "") -> Project:
        """Create a new project."""
        data = self._request(
            "POST",
            "/projects",
            json={"name": name, "description": description},
        ).json()
        return Project.model_validate(data)

    def delete_project(self, project_id: str) -> None:
        """Delete a project."""
        self._request("DELETE", f"/projects/{project_id}")

    def update_project(
        self,
        project_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Project:
        """Rename or re-describe a project."""
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        data = self._request("PUT", f"/projects/{project_id}", json=body).json()
        return Project.model_validate(data)

    # ---------------------------------------------------------------- databases
    def list_databases(self) -> List[Database]:
        """List all FASTA databases visible to the caller."""
        data = self._get_json("/databases")
        return [Database.model_validate(d) for d in data]

    def get_database(self, database_id: str) -> Database:
        """Fetch a single database by ID."""
        return Database.model_validate(self._get_json(f"/databases/{database_id}"))

    def upload_database(self, file_path: Union[str, pathlib.Path]) -> List[Database]:
        """Upload a FASTA file and register it as a database.

        Returns the list of created :class:`Database` records (one per file).
        """
        p = pathlib.Path(file_path)
        with p.open("rb") as fh:
            data = self._request(
                "PUT",
                "/databases",
                files={"file": (p.name, fh, "application/octet-stream")},
            ).json()
        return [Database.model_validate(d) for d in data]

    def update_database(self, database_id: str, *, name: Optional[str] = None) -> Database:
        """Update a database record (e.g. rename it)."""
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        data = self._request("PUT", f"/databases/{database_id}", json=body).json()
        return Database.model_validate(data)

    def delete_database(self, database_id: str) -> None:
        """Permanently delete a FASTA database."""
        self._request("DELETE", f"/databases/{database_id}")

    def get_database_download_url(self, database_id: str) -> str:
        """Return a presigned S3 URL to download the raw FASTA file."""
        data = self._get_json(f"/databases/{database_id}/download")
        return data if isinstance(data, str) else data["url"]

    def list_databases_by_project(self, project_id: str) -> List[Database]:
        """List databases shared into a specific project."""
        data = self._get_json(f"/databases/share-project/{project_id}")
        return [Database.model_validate(d) for d in data]

    # -------------------------------------------------------------- experiments
    def list_experiments(self) -> List[Experiment]:
        """List all experiments visible to the caller."""
        data = self._get_json("/experiments")
        return [Experiment.model_validate(e) for e in data]

    def list_experiments_by_project(self, project_id: str) -> List[Experiment]:
        """List all experiments belonging to a project."""
        data = self._get_json(f"/experiments/projects/{project_id}")
        return [Experiment.model_validate(e) for e in data]

    def get_experiment(self, experiment_id: str, project_id: str) -> Experiment:
        """Fetch a single experiment by ID."""
        return Experiment.model_validate(
            self._get_json(f"/experiments/{experiment_id}/{project_id}")
        )

    def create_experiment(
        self,
        *,
        name: str,
        description: str = "",
        project_id: str,
        tags: Optional[List[str]] = None,
    ) -> Experiment:
        """Create a new experiment inside a project."""
        body: dict[str, Any] = {"name": name, "description": description, "project_id": project_id}
        if tags is not None:
            body["tags"] = tags
        data = self._request("POST", "/experiments", json=body).json()
        return Experiment.model_validate(data)

    def delete_experiment(self, experiment_id: str, project_id: str) -> None:
        """Delete an experiment and all its associated files and searches."""
        self._request("DELETE", f"/experiments/{experiment_id}/{project_id}")

    def update_experiment(
        self,
        experiment_id: str,
        project_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Experiment:
        """Update an experiment's name, description, or tags."""
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if tags is not None:
            body["tags"] = tags
        data = self._request("PUT", f"/experiments/{experiment_id}/{project_id}", json=body).json()
        return Experiment.model_validate(data)

    def restore_experiment(self, experiment_id: str, project_id: str) -> None:
        """Trigger restore of a cold-archived experiment from S3 Glacier."""
        self._request("POST", f"/experiments/{experiment_id}/{project_id}/restore")

    def check_restore_status(self, experiment_id: str, project_id: str) -> Json:
        """Poll the restore status for a cold-archived experiment."""
        return self._get_json(f"/experiments/{experiment_id}/{project_id}/restore/status")

    def list_search_results_by_experiment(self, experiment_id: str) -> List[SearchResult]:
        """List all search results belonging to an experiment."""
        data = self._get_json(f"/experiments/{experiment_id}/search_results")
        return [SearchResult.model_validate(r) for r in data]

    # ----------------------------------------------------------- raw file upload
    def list_raw_files(self, experiment_id: str, project_id: str) -> List[RawFile]:
        """List raw files attached to an experiment."""
        data = self._get_json(f"/experiments/{experiment_id}/{project_id}/files")
        return [RawFile.model_validate(f) for f in data]

    def upload_raw_file(
        self,
        experiment_id: str,
        project_id: str,
        file_path: Union[str, pathlib.Path],
    ) -> None:
        """Upload a raw MS file (e.g. ``.raw``, ``.mzML``, Bruker ``.d``) to an experiment.

        The backend streams the file directly to S3 and automatically triggers
        mzparquet conversion for Thermo ``.raw`` and Bruker files.
        """
        p = pathlib.Path(file_path)
        with p.open("rb") as fh:
            self._request(
                "PUT",
                f"/experiments/{experiment_id}/{project_id}/files",
                files={"file": (p.name, fh, "application/octet-stream")},
            )

    def upload_mzparquet(
        self,
        experiment_id: str,
        project_id: str,
        file_path: Union[str, pathlib.Path],
    ) -> None:
        """Upload a pre-converted ``.mzparquet`` file to an experiment."""
        p = pathlib.Path(file_path)
        with p.open("rb") as fh:
            self._request(
                "PUT",
                f"/experiments/{experiment_id}/{project_id}/files/mzparquet",
                files={"file": (p.name, fh, "application/octet-stream")},
            )

    def delete_raw_file(self, experiment_id: str, file_id: str) -> None:
        """Permanently delete a raw file from an experiment."""
        self._request("DELETE", f"/experiments/{experiment_id}/files/{file_id}")

    def wait_for_file_ready(
        self,
        experiment_id: str,
        project_id: str,
        file_id: str,
        *,
        poll_interval: float = 5.0,
        timeout: float = 300.0,
    ) -> RawFile:
        """Block until a raw file's conversion job reaches a terminal state.

        Polls :meth:`list_raw_files` every *poll_interval* seconds.
        Raises ``TimeoutError`` if the file is not ready within *timeout* seconds.
        Raises :class:`NotFoundError` if *file_id* is not in the experiment.
        """
        deadline = time.monotonic() + timeout
        while True:
            files = self.list_raw_files(experiment_id, project_id)
            match = next((f for f in files if f.id == file_id), None)
            if match is None:
                raise NotFoundError(
                    f"File {file_id!r} not found in experiment {experiment_id!r}",
                    status_code=404,
                )
            if match.job_id is None or (
                match.job_status and match.job_status.upper() in ("SUCCEEDED", "FAILED")
            ):
                return match
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"File {file_id!r} did not finish converting within {timeout:.0f}s "
                    f"(last job_status: {match.job_status!r})"
                )
            time.sleep(min(poll_interval, remaining))

    # ---------------------------------------------------------- search submission
    def submit_search(self, experiment_id: str, project_id: str, params: Any) -> None:
        """Submit a Sage DDA search job.

        ``params`` is a dict matching the Sage search parameters JSON schema
        (``database``, ``precursor_tol``, ``fragment_tol``, etc.).
        """
        self._request(
            "POST",
            f"/experiments/{experiment_id}/{project_id}/search",
            json=params,
        )

    def submit_search_dia(self, experiment_id: str, project_id: str, params: Any) -> None:
        """Submit a DIA search job.

        ``params`` is a dict with at minimum a ``database`` key containing
        the spectral library reference and DIA-specific parameters.
        """
        self._request(
            "POST",
            f"/experiments/{experiment_id}/{project_id}/search-dia",
            json=params,
        )

    def submit_search_prm(self, experiment_id: str, project_id: str, params: Any) -> None:
        """Submit a PRM search job.

        ``params`` is a dict with a ``params`` key containing PRM-specific
        settings (``ms1_ppm_tolerance``, ``ms2_ppm_tolerance``, etc.).
        """
        self._request(
            "POST",
            f"/experiments/{experiment_id}/{project_id}/search-prm",
            json=params,
        )

    # --------------------------------------------------------- search results
    def wait_for_search(
        self,
        search_result_id: str,
        *,
        poll_interval: float = 5.0,
        timeout: float = 300.0,
    ) -> SearchResult:
        """Block until a search job reaches a terminal state.

        Polls :meth:`get_search_result` every *poll_interval* seconds.
        Raises ``TimeoutError`` if the search does not finish within *timeout* seconds.
        """
        _TERMINAL = frozenset({"SUCCEEDED", "FAILED", "COMPLETE", "ERROR"})
        deadline = time.monotonic() + timeout
        while True:
            result = self.get_search_result(search_result_id)
            if result.status and result.status.upper() in _TERMINAL:
                return result
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"Search {search_result_id!r} did not finish within {timeout:.0f}s "
                    f"(last status: {result.status!r})"
                )
            time.sleep(min(poll_interval, remaining))

    def list_search_results(self) -> List[SearchResult]:
        """List all search results visible to the caller."""
        data = self._get_json("/search_results")
        return [SearchResult.model_validate(r) for r in data]

    def get_search_result(self, search_result_id: str) -> SearchResult:
        """Fetch a single search result by ID."""
        return SearchResult.model_validate(
            self._get_json(f"/search_results/{search_result_id}")
        )

    def delete_search_result(self, search_result_id: str) -> None:
        """Permanently delete a search result."""
        self._request("DELETE", f"/search_results/{search_result_id}")

    def update_search_name(self, search_result_id: str, name: str) -> SearchResult:
        """Rename a search result."""
        data = self._request(
            "PUT", f"/search_results/{search_result_id}", json={"name": name}
        ).json()
        return SearchResult.model_validate(data)

    def download_search_results(
        self,
        search_result_id: str,
        dest_dir: Union[str, pathlib.Path],
    ) -> List[pathlib.Path]:
        """Download all output files for a search result.

        Calls ``GET /search_results/:id/download`` to get presigned S3 URLs,
        then fetches each file into *dest_dir*. Returns the list of local paths.
        """
        dest = pathlib.Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)
        payload = self._get_json(f"/search_results/{search_result_id}/download")
        if isinstance(payload, str):
            urls: list = [payload]
        elif isinstance(payload, list):
            urls = payload
        else:
            urls = payload.get("urls") or list(payload.values())
        paths: List[pathlib.Path] = []
        for url in urls:
            filename = pathlib.Path(url.split("?")[0].split("/")[-1])
            dest_file = dest / filename
            with httpx.stream("GET", url) as resp:
                resp.raise_for_status()
                with dest_file.open("wb") as fh:
                    for chunk in resp.iter_bytes(chunk_size=65536):
                        fh.write(chunk)
            paths.append(dest_file)
        return paths

    # -------------------------------------------------------- api-key management
    # The /api-keys endpoints exist primarily for the web UI, but are exposed
    # here so power users can rotate keys programmatically.
    def list_api_keys(self) -> List[ApiKey]:
        """List API keys belonging to the calling user."""
        data = self._get_json("/api-keys")
        return [ApiKey.model_validate(k) for k in data]

    def create_api_key(
        self,
        *,
        name: str,
        scopes: Optional[Iterable[str]] = None,
        expires_at: Optional[str] = None,
    ) -> CreatedApiKey:
        """Create a new API key.

        The returned :class:`CreatedApiKey` contains the plaintext ``key``
        attribute — store it now, it will never be shown again.
        """
        body: dict[str, Any] = {"name": name}
        if scopes is not None:
            body["scopes"] = list(scopes)
        if expires_at is not None:
            body["expires_at"] = expires_at
        data = self._request("POST", "/api-keys", json=body).json()
        return CreatedApiKey.model_validate(data)

    def revoke_api_key(self, api_key_id: str) -> None:
        """Revoke an API key by ID. Effective immediately."""
        self._request("DELETE", f"/api-keys/{api_key_id}")

    # ----------------------------------------------------- organization & users
    def get_organization_usage(self) -> OrgUsage:
        """Return storage and usage statistics for the caller's organization."""
        return OrgUsage.model_validate(self._get_json("/organization/usage"))

    def invite_to_organization(self, email: str) -> None:
        """Send an invitation e-mail to *email* to join the organization."""
        self._request("POST", "/organization/invite", json={"email": email})

    # ------------------------------------------------------- spectral libraries
    def list_spectral_libs(self) -> List[SpectralLib]:
        """List all spectral libraries visible to the caller."""
        data = self._get_json("/spectral-libs")
        return [SpectralLib.model_validate(s) for s in data]

    def get_spectral_lib(self, spectral_lib_id: str) -> SpectralLib:
        """Fetch a single spectral library by ID."""
        return SpectralLib.model_validate(self._get_json(f"/spectral-libs/{spectral_lib_id}"))

    def upload_spectral_lib(
        self,
        spectral_lib_id: str,
        file_path: Union[str, pathlib.Path],
    ) -> SpectralLib:
        """Upload a spectral library file to an existing spectral library record."""
        p = pathlib.Path(file_path)
        with p.open("rb") as fh:
            data = self._request(
                "PUT",
                f"/spectral-libs/{spectral_lib_id}/upload",
                files={"file": (p.name, fh, "application/octet-stream")},
            ).json()
        return SpectralLib.model_validate(data)

    def delete_spectral_lib(self, spectral_lib_id: str) -> None:
        """Permanently delete a spectral library."""
        self._request("DELETE", f"/spectral-libs/{spectral_lib_id}")

    def list_spectral_libs_by_project(self, project_id: str) -> List[SpectralLib]:
        """List spectral libraries shared into a specific project."""
        data = self._get_json(f"/spectral-libs/share-project/{project_id}")
        return [SpectralLib.model_validate(s) for s in data]

    # --------------------------------------------------------- search templates
    def list_search_params(self) -> List[Json]:
        """List saved search parameter templates."""
        return self._get_json("/search_params")

    def get_search_params(self, search_params_id: str) -> Json:
        """Fetch a single search parameter template by ID."""
        return self._get_json(f"/search_params/{search_params_id}")

    def create_search_params(self, params: Any) -> Json:
        """Save a search parameter template for reuse."""
        return self._request("POST", "/search_params", json=params).json()
