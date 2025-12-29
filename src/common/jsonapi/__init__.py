"""
JSON:API implementation for FastAPI.
Follows https://jsonapi.org/format/ specification.
"""

from .resources import (
    ResourceIdentifier,
    ResourceObject,
    ResourceObjectForCreation,
    SingleResourceRequest,
    SingleResourceResponse,
    CollectionResponse,
)
from .errors import (
    JsonApiError,
    JsonApiErrorResponse,
)

__all__ = [
    # Resources
    "ResourceIdentifier",
    "ResourceObject",
    "ResourceObjectForCreation",
    "SingleResourceRequest",
    "SingleResourceResponse",
    "CollectionResponse",
    # Errors
    "JsonApiError",
    "JsonApiErrorResponse",
]

__version__ = "0.1.0"
