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
    Peptide,
    PrmQuantRow,
    Project,
    ProteinPsm,
    PtmSite,
    QcDashboard,
    QcDashboardDia,
    SampleGroup,
    XicData,
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


# ---------------------------------------------------------------------------
# QC dashboard — DDA
# ---------------------------------------------------------------------------

def test_qc_dashboard_dda(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results/sr_1/qc/dashboard",
        json={
            "protein_ids": 1842,
            "peptide_ids": 9210,
            "psm_count": 45321,
            "protein_fdr": 0.009,
            "peptide_fdr": 0.008,
            "median_precursor_ppm": 2.1,
            "files": ["sample_A.raw", "sample_B.raw"],
        },
    )
    qc = client.qc_dashboard("sr_1")
    assert isinstance(qc, QcDashboard)
    assert qc.protein_ids == 1842
    assert qc.peptide_ids == 9210
    assert qc.protein_fdr == pytest.approx(0.009)
    assert len(qc.files) == 2


# ---------------------------------------------------------------------------
# QC dashboard — DIA
# ---------------------------------------------------------------------------

def test_qc_dashboard_dia(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results/sr_2/qc/dashboard_dia",
        json={
            "protein_ids": 5210,
            "peptide_ids": 28400,
            "median_cv": 8.3,
            "missing_value_rate": 0.04,
            "files": ["file1.mzML"],
        },
    )
    qc = client.qc_dashboard_dia("sr_2")
    assert isinstance(qc, QcDashboardDia)
    assert qc.median_cv == pytest.approx(8.3)
    assert qc.missing_value_rate == pytest.approx(0.04)


# ---------------------------------------------------------------------------
# Peptides
# ---------------------------------------------------------------------------

def test_get_peptides(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results/sr_1/peptides?page=1&per_page=100",
        json=[
            {
                "peptide": "GAPDH_PEPTIDE",
                "proteins": ["P04406"],
                "charge": 2,
                "q_value": 0.001,
                "score": 98.5,
                "rt": 32.4,
                "file": "sample_A.raw",
            },
            {
                "peptide": "ACTIN_PEPTIDE",
                "proteins": ["P60709"],
                "charge": 3,
                "q_value": 0.005,
                "score": 85.1,
                "rt": 18.9,
                "file": "sample_B.raw",
            },
        ],
    )
    peptides = client.get_peptides("sr_1")
    assert len(peptides) == 2
    assert all(isinstance(p, Peptide) for p in peptides)
    assert peptides[0].peptide == "GAPDH_PEPTIDE"
    assert peptides[0].charge == 2
    assert peptides[1].proteins == ["P60709"]


def test_get_peptides_pagination(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results/sr_1/peptides?page=2&per_page=50",
        json=[],
    )
    result = client.get_peptides("sr_1", page=2, per_page=50)
    assert result == []


# ---------------------------------------------------------------------------
# Protein PSMs — DDA and DIA
# ---------------------------------------------------------------------------

def test_get_protein_psms_dda(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results/sr_1/protein/P04406",
        json=[
            {"peptide": "GAPDH_PEP1", "charge": 2, "score": 95.0, "q_value": 0.001, "rt": 32.1, "file": "A.raw", "scan_num": 1234},
        ],
    )
    psms = client.get_protein_psms("sr_1", "P04406")
    assert len(psms) == 1
    assert isinstance(psms[0], ProteinPsm)
    assert psms[0].scan_num == 1234


def test_get_protein_psms_dia(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results/sr_2/protein/P04406/dia",
        json=[
            {"peptide": "GAPDH_PEP1", "charge": 2, "score": 88.0, "q_value": 0.002, "rt": 31.5, "file": "B.mzML"},
        ],
    )
    psms = client.get_protein_psms_dia("sr_2", "P04406")
    assert isinstance(psms[0], ProteinPsm)
    assert psms[0].file == "B.mzML"


# ---------------------------------------------------------------------------
# PTM sites
# ---------------------------------------------------------------------------

def test_get_all_ptm_sites(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results/sr_1/ptm_sites",
        json=[
            {"protein": "P04406", "peptide": "PHOSPHOPEP", "residue": "S", "position": 42, "mass": 79.966, "localization_score": 0.98, "q_value": 0.001},
        ],
    )
    sites = client.get_all_ptm_sites("sr_1")
    assert len(sites) == 1
    assert isinstance(sites[0], PtmSite)
    assert sites[0].residue == "S"
    assert sites[0].position == 42


def test_get_ptm_sites_by_protein(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results/sr_1/protein/P04406/ptm_sites",
        json=[
            {"protein": "P04406", "peptide": "PHOSPHOPEP", "residue": "T", "position": 99, "mass": 79.966, "localization_score": 0.95, "q_value": 0.005},
        ],
    )
    sites = client.get_ptm_sites("sr_1", "P04406")
    assert sites[0].residue == "T"


# ---------------------------------------------------------------------------
# XIC
# ---------------------------------------------------------------------------

def test_get_xic(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results/sr_1/xic/PEPTIDEK/2",
        json={
            "precursor": "PEPTIDEK/2",
            "file": "sample_A.raw",
            "apex_rt": 32.4,
            "points": [
                {"rt": 31.0, "intensity": 1200.0},
                {"rt": 32.4, "intensity": 95000.0},
                {"rt": 33.8, "intensity": 800.0},
            ],
        },
    )
    xic = client.get_xic("sr_1", "PEPTIDEK/2")
    assert isinstance(xic, XicData)
    assert xic.apex_rt == pytest.approx(32.4)
    assert len(xic.points) == 3
    assert xic.points[1].intensity == pytest.approx(95000.0)


# ---------------------------------------------------------------------------
# PRM quant
# ---------------------------------------------------------------------------

def test_get_prm_quant(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results_prm/prm_1/quant",
        json=[
            {"peptide": "TARGETPEP", "charge": 2, "level": "light", "replicate": 1, "file_path": "rep1.raw", "response": 1250000.0},
            {"peptide": "TARGETPEP", "charge": 2, "level": "light", "replicate": 2, "file_path": "rep2.raw", "response": 1340000.0},
        ],
    )
    rows = client.get_prm_quant("prm_1")
    assert len(rows) == 2
    assert all(isinstance(r, PrmQuantRow) for r in rows)
    assert rows[0].response == pytest.approx(1250000.0)
    assert rows[1].replicate == 2


# ---------------------------------------------------------------------------
# Sample groups
# ---------------------------------------------------------------------------

def test_get_sample_groups(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results/sr_1/groups",
        json=[
            {"file": "ctrl_1.raw", "group": "control", "label": "Control 1"},
            {"file": "treat_1.raw", "group": "treatment", "label": "Treatment 1"},
        ],
    )
    groups = client.get_sample_groups("sr_1")
    assert len(groups) == 2
    assert all(isinstance(g, SampleGroup) for g in groups)
    assert groups[0].group == "control"
    assert groups[1].file == "treat_1.raw"


def test_save_sample_groups(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results/sr_1/groups",
        method="PUT",
        json=[
            {"file": "ctrl_1.raw", "group": "control", "label": "Control 1"},
        ],
    )
    groups = [SampleGroup(file="ctrl_1.raw", group="control", label="Control 1")]
    result = client.save_sample_groups("sr_1", groups)
    assert result[0]["file"] == "ctrl_1.raw"


# ---------------------------------------------------------------------------
# Stream results
# ---------------------------------------------------------------------------

def test_stream_results_json(client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/search_results/sr_1/stream",
        method="POST",
        json={"peptides": [{"peptide": "STREAMPEP", "q_value": 0.001}]},
    )
    result = client.stream_results("sr_1")
    assert "peptides" in result
