"""Router registration and setup."""

from fastapi import FastAPI

from src.app.interfaces.http.controllers import (
    auth_controller,
    price_history_controller,
    product_controller,
    source_website_controller,
    user_controller,
    # search_config_controller,
)


def setup_routers(app: FastAPI) -> None:
    """
    Register all API routers for the application.

    Current routes:
    - /auth: Authentication endpoints (login, token refresh)
    - /users: User management endpoints (CRUD operations)
    - /products: Product tracking endpoints (CRUD operations)
    - /source-websites: Source website management endpoints (CRUD operations)
    - /price-histories: Price history tracking endpoints

    Future routes (commented out):
    - /search-configs: Search configuration management

    Args:
        app: FastAPI application instance
    """
    app.include_router(auth_controller)
    app.include_router(user_controller)
    app.include_router(product_controller)
    app.include_router(source_website_controller)
    app.include_router(price_history_controller)
