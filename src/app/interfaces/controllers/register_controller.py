from fastapi import APIRouter, Depends, HTTPException, status
from src.app.infrastructure.repositories.user_repository import UserRepository
from src.app.infrastructure.database_config import get_db
from src.app.use_cases.user_use_cases import CreateUserUseCase, pwd_context
from src.app.interfaces.schemas.user_schema import UserReadResponse, UserCreateRequest
from sqlalchemy.orm import Session

register_router = APIRouter(tags=["register"])


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@register_router.post(
    "/register", response_model=UserReadResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreateRequest, user_repo: UserRepository = Depends(get_user_repository)
):
    hashed_password = hash_password(user_data.password)
    use_case = CreateUserUseCase(user_repo)
    try:
        created_user = use_case.execute(user_data, hashed_password)
        return created_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
