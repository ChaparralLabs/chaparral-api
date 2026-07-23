"""Official Python client for the Chaparral proteomics platform.

Quick start::

    from chaparral import Client

    client = Client(api_key="chpr_live_...")
    for project in client.list_projects():
        print(project.id, project.name)

If ``api_key`` is omitted, ``Client`` reads ``CHAPARRAL_API_KEY`` from the
environment. The default base URL is ``https://api.chaparral.ai`` and can be
overridden with ``base_url=`` or the ``CHAPARRAL_BASE_URL`` env var.
"""

from chaparral.client import Client
from chaparral.exceptions import (
    ApiError,
    AuthenticationError,
    ChaparralError,
    NotFoundError,
    RateLimitError,
)
from chaparral.models import (
    ApiKey,
    CreatedApiKey,
    Database,
    Experiment,
    OrgUsage,
    Organization,
    Peptide,
    PrmPeptide,
    PrmQuantRow,
    PrmXicRow,
    Project,
    ProteinPsm,
    PtmSite,
    QcDashboard,
    QcDashboardDia,
    RawFile,
    SampleGroup,
    SearchResult,
    SpectralLib,
    XicData,
)

__all__ = [
    "ApiError",
    "ApiKey",
    "AuthenticationError",
    "ChaparralError",
    "Client",
    "CreatedApiKey",
    "Database",
    "Experiment",
    "NotFoundError",
    "OrgUsage",
    "Organization",
    "Peptide",
    "PrmPeptide",
    "PrmQuantRow",
    "PrmXicRow",
    "Project",
    "ProteinPsm",
    "PtmSite",
    "QcDashboard",
    "QcDashboardDia",
    "RawFile",
    "RateLimitError",
    "SampleGroup",
    "SearchResult",
    "SpectralLib",
    "XicData",
]

__version__ = "0.3.0"
