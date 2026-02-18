from typing import Any

from pydantic import BaseModel


class JsonApiError(BaseModel):
    """Represents an individual error in JSON:API format"""
    id: str | None = None
    status: str  # HTTP status code as string (e.g., "400", "422")
    code: str | None = None  # Application-specific error code
    title: str | None = None  # Brief error title
    detail: str | None = None  # Detailed description
    source: dict[str, Any] | None = None  # Problematic field (e.g., {"pointer": "/data/attributes/email"})
    meta: dict[str, Any] | None = None


class JsonApiErrorResponse(BaseModel):
    """Standard JSON:API response for errors"""
    errors: list[JsonApiError]
