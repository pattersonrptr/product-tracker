"""Router registration and setup."""

from fastapi import FastAPI

from src.app.interfaces.http.controllers import (
    auth_controller,
    user_controller,
    # product_controller,  # TODO: Implement Products module
    # source_website_controller,
    # price_history_controller,
    # search_config_controller,
)


def setup_routers(app: FastAPI) -> None:
    """
    Register all API routers for the application.
    
    Current routes:
    - /auth: Authentication endpoints (login, token refresh)
    - /users: User management endpoints (CRUD operations)
    
    Future routes (commented out):
    - /products: Product tracking endpoints
    - /source-websites: Source website management
    - /price-history: Price history queries
    - /search-configs: Search configuration management
    
    Args:
        app: FastAPI application instance
    """
    app.include_router(auth_controller)
    app.include_router(user_controller)
    # app.include_router(product_controller)  # TODO: Uncomment when implemented
