"""
JSON:API implementation for FastAPI.
Follows https://jsonapi.org/format/ specification.
"""

from .errors import (
    JsonApiError,
    JsonApiErrorResponse,
)
from .middleware import make_jsonapi_middleware
from .resources import (
    CollectionResponse,
    ResourceIdentifier,
    ResourceObject,
    ResourceObjectForCreation,
    SingleResourceRequest,
    SingleResourceResponse,
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
    # Middleware
    "make_jsonapi_middleware",
]

__version__ = "0.1.0"
