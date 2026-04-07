#!/usr/bin/env python3
"""
Initialize database with default data for development.
This script is idempotent - safe to run multiple times.

Creates default users and loads source websites + search configs from fixtures.
"""

import os
import sys

# Add src to path
sys.path.insert(0, "/src")

# Import the create_superuser function
from create_superuser import create_superuser_user  # type: ignore[import-not-found]


def create_default_users():
    """Create default admin and celery worker users if they don't exist."""
    # 1. Admin superuser
    create_superuser_user(
        username="admin",
        email="admin@example.com",
        password="admin",
        is_active=True,
        is_staff=True,
        is_superuser=True,
        skip_if_exists=True,
        quiet=False,
    )

    # 2. Celery worker user (used by scrapers to authenticate with the API)
    celery_username = os.getenv("CELERY_WORKER_USERNAME", "celery_user")
    celery_password = os.getenv("CELERY_WORKER_PASSWORD", "celery_user_password")
    create_superuser_user(
        username=celery_username,
        email=f"{celery_username}@example.com",
        password=celery_password,
        is_active=True,
        is_staff=True,
        is_superuser=False,
        skip_if_exists=True,
        quiet=False,
    )


def load_seed_data():
    """Load source websites and search configs from fixtures."""
    from src.scripts.load_fixtures import load_fixtures

    fixtures_to_load = ["source_websites", "search_configs"]
    print(f"Loading seed data: {fixtures_to_load}")
    load_fixtures(fixtures_to_load)
    print("✓ Seed data loaded (source websites + search configs)")


if __name__ == "__main__":
    try:
        print("Initializing development database...")
        create_default_users()
        load_seed_data()
        print("✓ Development database ready")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error initializing database: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
