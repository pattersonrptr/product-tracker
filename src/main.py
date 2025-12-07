from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from src.app.interfaces.controllers import (
#     product_controller,
# )
from src.app.interfaces.controllers import (
    user_controller,
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

# app.include_router(product_controller.router)
# app.include_router(price_history_controller.router)
# app.include_router(source_website_controller.router)
# app.include_router(search_config_controller.router)
app.include_router(user_controller.router)
# app.include_router(user_controller.auth_router)
# app.include_router(user_controller.register_router)
