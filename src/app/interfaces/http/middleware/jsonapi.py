"""JSON:API content-type middleware."""

from fastapi import Request


async def jsonapi_content_type_middleware(request: Request, call_next):
    """
    Set default Content-Type to 'application/vnd.api+json' for JSON:API endpoints.
    
    Currently applied to paths starting with '/users' or '/auth'.
    This ensures compliance with JSON:API specification for these endpoints.
    
    Args:
        request: FastAPI Request object
        call_next: Next middleware in chain
        
    Returns:
        Response object with adjusted Content-Type if applicable
    """
    response = await call_next(request)

    try:
        path = request.url.path or ""
        if response.media_type == "application/json" and (
            path.startswith("/users") or path.startswith("/auth")
        ):
            response.media_type = "application/vnd.api+json"
    except Exception:
        # Silently ignore any errors in content-type adjustment
        pass

    return response
