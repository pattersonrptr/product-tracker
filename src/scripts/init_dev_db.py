#!/usr/bin/env python3
"""
Initialize database with default superuser for development.
This script is idempotent - safe to run multiple times.

Uses create_superuser.py internally for consistent user creation.
"""
import sys

# Add src to path
sys.path.insert(0, '/src')

# Import the create_superuser function
from create_superuser import create_superuser_user  # type: ignore[import-not-found]


def create_default_superuser():
    """Create default admin user if it doesn't exist."""
    print("Initializing development database...")

    try:
        create_superuser_user(
            username="admin",
            email="admin@example.com",
            password="admin",
            is_active=True,
            is_staff=True,
            is_superuser=True,
            skip_if_exists=True,  # Don't fail if already exists
            quiet=False,
        )
    except Exception as e:
        print(f"✗ Error creating superuser: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        create_default_superuser()
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error initializing database: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
