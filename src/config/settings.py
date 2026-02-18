import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Security & JWT Configuration
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "MY_SECRET_KEY",  # ⚠️ Change this in production!
)
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Logging Configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")  # development, production
ENABLE_JSON_LOGS = os.environ.get("ENABLE_JSON_LOGS", "false").lower() == "true"
