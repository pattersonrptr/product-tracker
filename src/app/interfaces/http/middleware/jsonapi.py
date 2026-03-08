"""JSON:API content-type middleware."""

from fastapi_jsonapi.middleware import make_jsonapi_middleware

jsonapi_content_type_middleware = make_jsonapi_middleware(
    path_prefixes=["/users", "/auth"]
)
