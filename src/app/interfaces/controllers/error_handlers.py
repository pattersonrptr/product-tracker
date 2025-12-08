import logging
from typing import List

from fastapi.exceptions import RequestValidationError
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from src.app.interfaces.schemas.jsonapi_errors import JsonApiError, JsonApiErrorResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _pydantic_error_to_jsonapi(err: dict) -> JsonApiError:
    """
    Converte um erro Pydantic (item de exc.errors()) em JsonApiError.
    Tenta montar um pointer amigável para /data/attributes/...
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
    Handler para RequestValidationError (erros de validação Pydantic / FastAPI).
    Retorna JSON:API errors[] com status 422.
    """
    try:
        errors: List[JsonApiError] = [_pydantic_error_to_jsonapi(e) for e in exc.errors()]
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
    Handler para HTTPException.
    - Se exc.detail já contém estrutura JSON:API (errors), devolve direto.
    - Caso contrário, encapsula a mensagem em errors[].
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
    Handler para exceções não tratadas — log e resposta 500 JSON:API.
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
