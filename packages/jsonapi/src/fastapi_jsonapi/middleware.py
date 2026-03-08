"""JSON:API content-type middleware for FastAPI."""

from collections.abc import Callable

from fastapi import Request


def make_jsonapi_middleware(
    path_prefixes: list[str] | None = None,
) -> Callable:
    """
    Create a JSON:API content-type middleware.

    Sets the response Content-Type to ``application/vnd.api+json`` for routes
    that return ``application/json``.

    Args:
        path_prefixes: Optional list of URL path prefixes to restrict the
            middleware to (e.g. ``["/users", "/auth"]``).  When *None* the
            middleware applies to every route.

    Returns:
        An async middleware callable suitable for use with
        ``app.middleware("http")``.
    """

    async def middleware(request: Request, call_next: Callable):
        response = await call_next(request)

        try:
            path = request.url.path or ""
            should_apply = path_prefixes is None or any(
                path.startswith(prefix) for prefix in path_prefixes
            )
            if response.media_type == "application/json" and should_apply:
                response.media_type = "application/vnd.api+json"
        except Exception:
            # Silently ignore any errors in content-type adjustment
            pass

        return response

    return middleware
