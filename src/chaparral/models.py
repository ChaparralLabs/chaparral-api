"""Pydantic models mirroring the JSON shapes returned by ``ch-backend``.

These are kept intentionally permissive (``model_config = ConfigDict(extra="allow")``)
so the SDK does not break when the server adds new fields. Each model exposes
the documented fields as typed attributes; anything extra is accessible via
``model.model_extra``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Organization(_Base):
    id: str
    name: str
    created_at: Optional[datetime] = None


class Project(_Base):
    id: str
    name: str
    description: Optional[str] = None
    organization_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class Database(_Base):
    """A FASTA database (proteome) registered with Chaparral."""

    id: str
    name: str
    organism: Optional[str] = None
    decoy_tag: Optional[str] = None
    organization_id: Optional[str] = None
    created_at: Optional[datetime] = None


class Experiment(_Base):
    """A collection of raw files and their associated searches."""

    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    storage_bytes: Optional[int] = None
    storage_status: Optional[str] = None


class RawFile(_Base):
    """A raw MS data file (or converted mzparquet) attached to an experiment."""

    id: str
    file: str
    extension: str
    size: int
    project_id: str
    experiment_id: Optional[str] = None
    organization_id: str
    created_at: datetime
    job_id: Optional[str] = None
    job_status: Optional[str] = None
    storage_status: Optional[str] = None


class SearchResult(_Base):
    id: str
    name: Optional[str] = None
    project_id: Optional[str] = None
    experiment_id: Optional[str] = None
    status: Optional[str] = None
    program: Optional[str] = None
    created_at: Optional[datetime] = None


class SpectralLib(_Base):
    """A DIA/PRM spectral library."""

    id: str
    name: Optional[str] = None
    organism: Optional[str] = None
    organization_id: Optional[str] = None
    created_at: Optional[datetime] = None
    storage_status: Optional[str] = None


class OrgUsage(_Base):
    """Organization storage and usage statistics."""

    storage_bytes: Optional[int] = None
    storage_limit_bytes: Optional[int] = None
    experiment_count: Optional[int] = None
    user_count: Optional[int] = None


class ApiKey(_Base):
    """API key metadata (the plaintext secret is never returned by list)."""

    id: str
    name: str
    prefix: str
    scopes: List[str] = Field(default_factory=list)
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class CreatedApiKey(ApiKey):
    """Returned only by ``Client.create_api_key`` — contains the plaintext
    secret. Show it to the user once and discard."""

    key: str


# Generic alias for endpoints that return raw JSON we haven't modelled yet.
Json = Any


# ── QC models ─────────────────────────────────────────────────────────────────

class QcDashboard(_Base):
    """DDA QC summary dashboard returned by ``/search_results/:id/qc/dashboard``."""

    protein_ids: Optional[int] = None
    peptide_ids: Optional[int] = None
    psm_count: Optional[int] = None
    protein_fdr: Optional[float] = None
    peptide_fdr: Optional[float] = None
    median_precursor_ppm: Optional[float] = None
    files: Optional[List[Any]] = None


class QcDashboardDia(_Base):
    """DIA QC summary dashboard returned by ``/search_results/:id/qc/dashboard_dia``."""

    protein_ids: Optional[int] = None
    peptide_ids: Optional[int] = None
    median_cv: Optional[float] = None
    missing_value_rate: Optional[float] = None
    files: Optional[List[Any]] = None


# ── Result row models ──────────────────────────────────────────────────────────

class Peptide(_Base):
    """A peptide identification row."""

    peptide: Optional[str] = None
    proteins: Optional[List[str]] = None
    charge: Optional[int] = None
    q_value: Optional[float] = None
    score: Optional[float] = None
    posterior_error: Optional[float] = None
    hyperscore: Optional[float] = None
    delta_next: Optional[float] = None
    rt: Optional[float] = None
    file: Optional[str] = None


class ProteinPsm(_Base):
    """A PSM (peptide-spectrum match) row for a given protein."""

    peptide: Optional[str] = None
    charge: Optional[int] = None
    score: Optional[float] = None
    q_value: Optional[float] = None
    rt: Optional[float] = None
    file: Optional[str] = None
    scan_num: Optional[int] = None


class PtmSite(_Base):
    """A post-translational modification site."""

    protein: Optional[str] = None
    peptide: Optional[str] = None
    residue: Optional[str] = None
    position: Optional[int] = None
    mass: Optional[float] = None
    localization_score: Optional[float] = None
    q_value: Optional[float] = None


class XicPoint(_Base):
    """A single point in an XIC chromatogram."""

    rt: float
    intensity: float


class XicData(_Base):
    """XIC chromatogram data for a precursor."""

    precursor: Optional[str] = None
    file: Optional[str] = None
    apex_rt: Optional[float] = None
    points: Optional[List[XicPoint]] = None


# ── PRM models ─────────────────────────────────────────────────────────────────

class PrmPeptide(_Base):
    """A peptide row from a PRM search result."""

    precursor: Optional[str] = None
    proteins: Optional[str] = None
    discriminant_score: Optional[float] = None
    apex_rt: Optional[float] = None
    q_value: Optional[float] = None


class PrmQuantRow(_Base):
    """A quantification data row from ``/search_results_prm/:id/quant``."""

    peptide: Optional[str] = None
    charge: Optional[int] = None
    level: Optional[str] = None
    replicate: Optional[int] = None
    file_path: Optional[str] = None
    response: Optional[float] = None


class PrmXicRow(_Base):
    """An XIC row from ``/search_results_prm/:id/xic``."""

    precursor: Optional[str] = None
    proteins: Optional[str] = None
    path: Optional[str] = None
    discriminant_score: Optional[float] = None
    apex_rt: Optional[float] = None
    rt_start: Optional[float] = None
    rt_end: Optional[float] = None
    retention_times: Optional[str] = None
    fragment_intensities: Optional[str] = None


# ── Pathway / GO models ────────────────────────────────────────────────────────

class SampleGroup(_Base):
    """A sample group assignment for multi-condition analysis."""

    file: Optional[str] = None
    group: Optional[str] = None
    label: Optional[str] = None
