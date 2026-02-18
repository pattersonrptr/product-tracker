import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.common.jsonapi import JsonApiError, JsonApiErrorResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _pydantic_error_to_jsonapi(err: dict) -> JsonApiError:
    """
    Converts a Pydantic error (item from exc.errors()) to JsonApiError.
    Attempts to build a friendly pointer to /data/attributes/...
    """
    loc = err.get("loc", [])
    msg = err.get("msg", "")
    typ = err.get("type", "")
    pointer = "/"
    if "attributes" in loc:
        try:
            idx = loc.index("attributes")
            after = loc[idx + 1 :]
            pointer = "/data/attributes" + "".join(f"/{p}" for p in after)
        except Exception:
            pointer = "/" + "/".join(str(p) for p in loc if p != "__root__")
    else:
        pointer = "/" + "/".join(str(p) for p in loc if p != "__root__")

    return JsonApiError(
        status="422",
        code="VALIDATION_ERROR",
        title="Validation error",
        detail=f"{msg} ({typ})",
        source={"pointer": pointer},
    )


async def handle_request_validation_error(request: Request, exc: RequestValidationError):
    """
    Handler for RequestValidationError (Pydantic / FastAPI validation errors).
    Returns JSON:API errors[] with status 422.
    """
    try:
        errors: list[JsonApiError] = [_pydantic_error_to_jsonapi(e) for e in exc.errors()]
    except Exception as e:
        logger.exception("Error mapping validation errors: %s", e)
        errors = [
            JsonApiError(
                status="422",
                code="VALIDATION_ERROR",
                title="Validation error",
                detail="Invalid request",
            )
        ]
    payload = JsonApiErrorResponse(errors=errors).model_dump()
    return JSONResponse(status_code=422, content=payload, media_type="application/vnd.api+json")


async def handle_http_exception(request: Request, exc: HTTPException):
    """
    Handler for HTTPException.
    - If exc.detail already contains JSON:API structure (errors), returns it directly.
    - Otherwise, wraps the message in errors[].
    """
    detail = exc.detail
    if isinstance(detail, dict) and "errors" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail, media_type="application/vnd.api+json")

    error = JsonApiError(
        status=str(exc.status_code),
        code="HTTP_ERROR",
        title="HTTP error",
        detail=str(detail),
    )
    payload = JsonApiErrorResponse(errors=[error]).model_dump()
    return JSONResponse(status_code=exc.status_code, content=payload, media_type="application/vnd.api+json")


async def handle_generic_exception(request: Request, exc: Exception):
    """
    Handler for unhandled exceptions — log and return 500 JSON:API response.
    """
    logger.exception("Unhandled exception: %s", exc)
    error = JsonApiError(
        status="500",
        code="INTERNAL_ERROR",
        title="Internal server error",
        detail="An unexpected error occurred.",
    )
    payload = JsonApiErrorResponse(errors=[error]).model_dump()
    return JSONResponse(status_code=500, content=payload, media_type="application/vnd.api+json")
