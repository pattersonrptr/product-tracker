#!/usr/bin/env python3
"""
Script to create the first superuser.
Run this ONCE to create your admin account.

Usage:
    python src/scripts/create_superuser.py
"""

import sys
from getpass import getpass
from sqlalchemy.orm import Session

from src.app.infrastructure.database_config import SessionLocal
from src.app.infrastructure.repositories.user_repository import UserRepository
from src.app.entities.user import User as UserEntity
from src.app.use_cases.user_use_cases import pwd_context


def create_superuser():
    """Create the first superuser account."""
    print("=" * 60)
    print("CREATE SUPERUSER")
    print("=" * 60)
    
    # Get user input
    username = input("Username: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        sys.exit(1)
    
    email = input("Email: ").strip()
    if not email:
        print("❌ Email cannot be empty!")
        sys.exit(1)
    
    password = getpass("Password: ")
    if not password:
        print("❌ Password cannot be empty!")
        sys.exit(1)
    
    password_confirm = getpass("Password (again): ")
    if password != password_confirm:
        print("❌ Passwords don't match!")
        sys.exit(1)
    
    # Create database session
    db: Session = SessionLocal()
    user_repo = UserRepository(db)
    
    try:
        # Check if username already exists
        existing_user = user_repo.get_by_username(username)
        if existing_user:
            print(f"❌ Username '{username}' already exists!")
            sys.exit(1)
        
        # Check if email already exists
        existing_email = user_repo.get_by_email(email)
        if existing_email:
            print(f"❌ Email '{email}' already exists!")
            sys.exit(1)
        
        # Hash password
        hashed_password = pwd_context.hash(password)
        
        # Create superuser entity
        superuser = UserEntity(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        
        # Save to database
        created_user = user_repo.create(superuser)
        
        print("\n" + "=" * 60)
        print("✅ Superuser created successfully!")
        print("=" * 60)
        print(f"Username: {created_user.username}")
        print(f"Email: {created_user.email}")
        print(f"Is Active: {created_user.is_active}")
        print(f"Is Staff: {created_user.is_staff}")
        print(f"Is Superuser: {created_user.is_superuser}")
        print("=" * 60)
        print("\n🎉 You can now login with these credentials!")
        
    except Exception as e:
        print(f"\n❌ Error creating superuser: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_superuser()
