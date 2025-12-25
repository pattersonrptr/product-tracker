from fastapi import APIRouter, Depends, HTTPException, status

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordRequestForm
from src.config import settings
from src.config.logging_config import get_logger
from src.app.infrastructure.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session
from src.app.interfaces.http.schemas.auth_schema import (
    TokenPayload,
    TokenResponse,
    TokenValidationResponse,
    TokenValidationRequest,
)
from src.app.interfaces.http.presenters.auth_presenter import AuthPresenter
from src.app.entities.user import User as UserEntity
from src.app.security.auth import get_current_active_user

from src.app.use_cases.user_use_cases import (
    GetUserByUsernameUseCase,
    pwd_context,
)
from src.app.infrastructure.database_config import get_db

auth_router = APIRouter(tags=["auth"], prefix="/auth")
logger = get_logger(__name__)

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


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Authenticate user and return JWT token in JSON:API format.
    
    Returns:
        TokenResponse: JSON:API formatted token response with user metadata
    """
    logger.info(f"Login attempt for username: {form_data.username}")
    
    get_user_by_username_uc = GetUserByUsernameUseCase(user_repo)
    user = get_user_by_username_uc.execute(form_data.username)

    if not user:
        logger.warning(
            f"Login failed: User not found - {form_data.username}",
            extra={'username': form_data.username, 'reason': 'user_not_found'}
        )
        return AuthPresenter.handle_invalid_credentials()
    
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(
            f"Login failed: Invalid password for user - {form_data.username}",
            extra={'username': form_data.username, 'user_id': user.id, 'reason': 'invalid_password'}
        )
        return AuthPresenter.handle_invalid_credentials()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "email": user.email},
        expires_delta=access_token_expires,
    )
    
    logger.info(
        f"Login successful for user: {user.username} (ID: {user.id})",
        extra={
            'action': 'login_success',
            'user_id': user.id,
            'username': user.username,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser
        }
    )
    
    return AuthPresenter.present_token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        meta={
            "user_id": user.id,
            "username": user.username,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }
    )


@auth_router.post("/verify-token", response_model=TokenValidationResponse)
async def verify_token(request: TokenValidationRequest):
    """
    Verify if a JWT token is valid.
    
    Request body (JSON:API):
        {
            "data": {
                "type": "token-validations",
                "attributes": {
                    "token": "your-jwt-token-here"
                }
            }
        }
    
    Returns:
        TokenValidationResponse: JSON:API formatted validation result
    """
    token = request.data.attributes.token
    
    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logger.debug("Token verification successful")
        return AuthPresenter.present_token_validation(
            is_valid=True,
            message="Token is valid"
        )
    except JWTError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        return AuthPresenter.present_token_validation(
            is_valid=False,
            message=f"Token verification failed: {str(e)}"
        )


@auth_router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(current_user: UserEntity = Depends(get_current_active_user)):
    """
    Refresh an existing JWT token.
    
    Returns:
        TokenResponse: JSON:API formatted token response
    """
    logger.info(
        f"Token refresh for user: {current_user.username} (ID: {current_user.id})",
        extra={'action': 'refresh_token', 'user_id': current_user.id}
    )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={
            "sub": current_user.username,
            "user_id": current_user.id,
            "email": current_user.email,
        },
        expires_delta=access_token_expires,
    )
    
    return AuthPresenter.present_token(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        meta={
            "user_id": current_user.id,
            "username": current_user.username,
        }
    )
