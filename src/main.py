from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize logging FIRST (before any other imports that might log)
from src.config.logging_config import setup_logging, get_logger
from src.config import settings

setup_logging(
    app_name="product-tracker",
    log_level=settings.LOG_LEVEL,
    enable_console=True,
    enable_file=True,
    json_logs=settings.ENABLE_JSON_LOGS,
)

logger = get_logger(__name__)

# from src.app.interfaces.http.controllers import (
#     product_controller,
# )
from src.app.interfaces.http.controllers import (
    user_controller,
    auth_controller,
    # source_website_controller,
    # price_history_controller,
    # search_config_controller,
)

from src.app.infrastructure.database import models  # noqa: F401

logger.info(f"Starting Product Tracker API in {settings.ENVIRONMENT} mode")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
import time
from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing information."""
    start_time = time.time()
    
    # Log incoming request
    logger.info(
        f"→ Request: {request.method} {request.url.path}",
        extra={
            'method': request.method,
            'path': request.url.path,
            'client_host': request.client.host if request.client else None
        }
    )
    
    # Process request
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        log_level = logger.info if response.status_code < 400 else logger.error
        log_level(
            f"← Response: {request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)",
            extra={
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms
            }
        )
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.exception(
            f"✗ Error: {request.method} {request.url.path} ({duration_ms:.2f}ms): {str(e)}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'duration_ms': duration_ms
            }
        )
        raise

# Register routers
app.include_router(auth_controller)
app.include_router(user_controller)

# Register global exception handlers (JSON:API)
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from src.app.interfaces.http.controllers.error_handlers import (
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
    Adjusts the media_type to 'application/vnd.api+json' for JSON:API endpoints.
    Currently applied to paths starting with '/users'.
    """
    response = await call_next(request)
    try:
        path = request.url.path or ""
        if response.media_type == "application/json" and path.startswith("/users"):
            response.media_type = "application/vnd.api+json"
    except Exception:
        pass
    return response
