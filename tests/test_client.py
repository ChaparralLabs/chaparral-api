"""Smoke tests against a mocked HTTP transport.

These don't talk to a real server; they verify the SDK's request shape,
auth header, error mapping, and pydantic parsing.
"""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from chaparral import (
    AuthenticationError,
    Client,
    CreatedApiKey,
    NotFoundError,
    Project,
)

BASE_URL = "https://api.example.test"
KEY = "chpr_live_TEST1234_SECRETSECRETSECRETSECRETSE"


@pytest.fixture()
def client() -> Client:
    return Client(api_key=KEY, base_url=BASE_URL)


def test_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CHAPARRAL_API_KEY", raising=False)
    with pytest.raises(AuthenticationError):
        Client()


def test_list_projects(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/projects",
        json=[
            {"id": "proj_1", "name": "Alpha"},
            {"id": "proj_2", "name": "Beta", "tags": ["dia"]},
        ],
        match_headers={"Authorization": f"Bearer {KEY}"},
    )
    projects = client.list_projects()
    assert [p.id for p in projects] == ["proj_1", "proj_2"]
    assert isinstance(projects[0], Project)
    assert projects[1].tags == ["dia"]


def test_get_project_not_found(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/projects/missing",
        status_code=404,
        json={"message": "not found"},
    )
    with pytest.raises(NotFoundError) as exc:
        client.get_project("missing")
    assert exc.value.status_code == 404


def test_create_api_key(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/api-keys",
        method="POST",
        json={
            "id": "ak_1",
            "name": "ci",
            "prefix": "ABC12345",
            "scopes": ["full_access"],
            "created_at": "2026-05-06T00:00:00Z",
            "key": "chpr_live_ABC12345_FULLSECRETHERE",
        },
    )
    created = client.create_api_key(name="ci")
    assert isinstance(created, CreatedApiKey)
    assert created.key.startswith("chpr_live_")
