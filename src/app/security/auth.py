from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from src.config import settings
from src.app.infrastructure.repositories.user_repository import UserRepository
from src.app.infrastructure.database_config import get_db
from sqlalchemy.orm import Session

reusable_oauth2 = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=401, detail="Could not validate credentials"
            )
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(username=username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
