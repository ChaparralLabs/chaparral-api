"""Synchronous Chaparral API client.

The client is a thin, typed wrapper around ``ch-backend``'s REST endpoints.
Authentication uses a long-lived API key (``Authorization: Bearer chpr_...``)
that the user issues from the Chaparral web UI under Settings → API Keys.
"""

from __future__ import annotations

import os
from typing import Any, Iterable, List, Mapping, Optional

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
    Json,
    Organization,
    Project,
    SearchResult,
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
        user_agent: str = "chaparral-python/0.1.0",
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
    ) -> httpx.Response:
        try:
            resp = self._http.request(
                method,
                path,
                params=params,
                json=json,
                content=content,
                headers=headers,
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

    # ---------------------------------------------------------------- databases
    def list_databases(self) -> List[Database]:
        """List all FASTA databases visible to the caller."""
        data = self._get_json("/fasta")
        return [Database.model_validate(d) for d in data]

    def get_database(self, database_id: str) -> Database:
        """Fetch a single database by ID."""
        return Database.model_validate(self._get_json(f"/fasta/{database_id}"))

    # --------------------------------------------------------- search results
    def list_search_results(self) -> List[SearchResult]:
        """List all search results visible to the caller."""
        data = self._get_json("/search_results")
        return [SearchResult.model_validate(r) for r in data]

    def get_search_result(self, search_result_id: str) -> SearchResult:
        """Fetch a single search result by ID."""
        return SearchResult.model_validate(
            self._get_json(f"/search_results/{search_result_id}")
        )

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
