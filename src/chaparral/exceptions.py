"""Exception hierarchy raised by the Chaparral client.

All errors raised by the client inherit from :class:`ChaparralError`, so a
single ``except ChaparralError`` clause catches everything the SDK can throw.
"""

from __future__ import annotations

from typing import Any, Optional


class ChaparralError(Exception):
    """Base class for every error raised by the Chaparral client."""


class ApiError(ChaparralError):
    """Raised when the server returns a non-2xx response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"[{self.status_code}] {super().__str__()}"


class AuthenticationError(ApiError):
    """401 — bad / missing / revoked / expired API key."""


class NotFoundError(ApiError):
    """404 — resource not found."""


class RateLimitError(ApiError):
    """429 — too many requests."""
