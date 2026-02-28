"""
HTTP Controllers (Adapters for HTTP requests/responses).
"""

from src.app.interfaces.http.controllers.auth_controller import (
    auth_router as auth_controller,
)
from src.app.interfaces.http.controllers.price_history_controller import (
    router as price_history_controller,
)
from src.app.interfaces.http.controllers.product_controller import (
    router as product_controller,
)
from src.app.interfaces.http.controllers.source_website_controller import (
    router as source_website_controller,
)
from src.app.interfaces.http.controllers.user_controller import (
    router as user_controller,
)

__all__ = [
    "user_controller",
    "auth_controller",
    "product_controller",
    "source_website_controller",
    "price_history_controller",
]
