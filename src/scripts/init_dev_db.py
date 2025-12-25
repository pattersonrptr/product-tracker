#!/usr/bin/env python3
"""
Initialize database with default superuser for development.
This script is idempotent - safe to run multiple times.
"""
import sys
import os

# Add src to path
sys.path.insert(0, '/src')

from sqlalchemy.orm import Session
from src.app.infrastructure.database_config import engine
from src.app.infrastructure.repositories.user_repository import UserRepository
from src.app.use_cases.user_use_cases import CreateUserUseCase, pwd_context
from src.app.entities.user import User as UserEntity
from src.app.interfaces.http.schemas.user_schema import UserCreateRequest, UserResourceForCreation, UserAttributesForCreation

def create_default_superuser():
    """Create default admin user if it doesn't exist."""
    db = Session(engine)
    user_repo = UserRepository(db)
    
    # Check if admin user already exists
    existing_user = user_repo.get_by_username("admin")
    
    if existing_user:
        print("✓ Superuser 'admin' already exists. Skipping creation.")
        db.close()
        return
    
    print("Creating default superuser 'admin'...")
    
    # Create admin user
    user_data = UserCreateRequest(
        data=UserResourceForCreation(
            type="users",
            attributes=UserAttributesForCreation(
                username="admin",
                email="admin@example.com",
                password="admin",
                is_active=True,
                is_staff=True,
                is_superuser=True,
            )
        )
    )
    
    hashed_password = pwd_context.hash("admin")
    create_user_uc = CreateUserUseCase(user_repo)
    created_user = create_user_uc.execute(user_data, hashed_password)
    
    print(f"✓ Superuser created: {created_user.username} (ID: {created_user.id})")
    print(f"  Username: admin")
    print(f"  Password: admin")
    print(f"  Email: {created_user.email}")
    
    db.close()

if __name__ == "__main__":
    try:
        create_default_superuser()
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error creating superuser: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
