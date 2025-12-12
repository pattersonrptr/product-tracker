from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class JsonApiError(BaseModel):
    """Represents an individual error in JSON:API format"""
    id: Optional[str] = None
    status: str  # HTTP status code as string (e.g., "400", "422")
    code: Optional[str] = None  # Application-specific error code
    title: Optional[str] = None  # Brief error title
    detail: Optional[str] = None  # Detailed description
    source: Optional[Dict[str, Any]] = None  # Problematic field (e.g., {"pointer": "/data/attributes/email"})
    meta: Optional[Dict[str, Any]] = None


class JsonApiErrorResponse(BaseModel):
    """Standard JSON:API response for errors"""
    errors: List[JsonApiError]
