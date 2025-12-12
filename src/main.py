from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from src.app.interfaces.controllers import (
#     product_controller,
# )
from src.app.interfaces.controllers import (
    user_controller,
    auth_controller,
    register_controller,
    # source_website_controller,
    # price_history_controller,
    # search_config_controller,
)

from src.app.infrastructure.database import models  # noqa: F401

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_controller.auth_router)
app.include_router(register_controller.register_router)
app.include_router(user_controller.router)

# Register global exception handlers (JSON:API)
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from src.app.interfaces.controllers.error_handlers import (
    handle_request_validation_error,
    handle_http_exception,
    handle_generic_exception,
)

app.add_exception_handler(RequestValidationError, handle_request_validation_error)
app.add_exception_handler(HTTPException, handle_http_exception)
app.add_exception_handler(Exception, handle_generic_exception)


# Middleware to set default Content-Type for JSON:API endpoints
@app.middleware("http")
async def set_default_jsonapi_content_type(request, call_next):
    """
    Ajusta o media_type para 'application/vnd.api+json' para endpoints JSON:API.
    Atualmente aplicado para paths que começam com '/users'.
    """
    response = await call_next(request)
    try:
        path = request.url.path or ""
        if response.media_type == "application/json" and path.startswith("/users"):
            response.media_type = "application/vnd.api+json"
    except Exception:
        pass
    return response
