from fastapi import APIRouter, Depends, HTTPException, status

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordRequestForm
from src.config import settings
from src.app.infrastructure.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session
from src.app.interfaces.schemas.auth_schema import TokenPayload
from src.app.entities.user import User as UserEntity
from src.app.security.auth import get_current_active_user

from src.app.use_cases.user_use_cases import (
    GetUserByUsernameUseCase,
    pwd_context,
)
from src.app.infrastructure.database_config import get_db

auth_router = APIRouter(tags=["auth"], prefix="/auth")

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


@auth_router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository),
):
    get_user_by_username_uc = GetUserByUsernameUseCase(user_repo)
    user = get_user_by_username_uc.execute(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "email": user.email},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/verify-token")
async def verify_token(payload: TokenPayload):
    try:
        jwt.decode(payload.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return {"is_valid": True}
    except JWTError:
        return {"is_valid": False}


@auth_router.post("/refresh-token")
async def refresh_token(current_user: UserEntity = Depends(get_current_active_user)):
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={
            "sub": current_user.username,
            "user_id": current_user.id,
            "email": current_user.email,
        },
        expires_delta=access_token_expires,
    )
    return {"access_token": new_access_token, "token_type": "bearer"}
