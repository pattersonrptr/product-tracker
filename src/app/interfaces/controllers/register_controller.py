from fastapi import APIRouter, Depends, status
from src.app.domain.validators.user_validator import UserValidator
from src.app.infrastructure.repositories.user_repository import UserRepository
from src.app.infrastructure.database_config import get_db
from src.app.use_cases.user_use_cases import CreateUserUseCase, pwd_context
from src.app.interfaces.schemas.user_schema import UserReadResponse, UserCreateRequest
from sqlalchemy.orm import Session
from src.app.interfaces.response_handlers.user_response_handler import UserResponseHandler

register_router = APIRouter(tags=["register"])


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@register_router.post(
    "/register", response_model=UserReadResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_in: UserCreateRequest, user_repo: UserRepository = Depends(get_user_repository)
):
    validator = UserValidator(user_repo)
    validation_errors = validator.validate_create_request(user_in)
    
    if validation_errors:
        return UserResponseHandler.handle_validation_errors(validation_errors)

    attrs = user_in.data.attributes
    hashed_password = hash_password(attrs.password)
    use_case = CreateUserUseCase(user_repo)
    created_user = use_case.execute(user_in, hashed_password)
    return UserResponseHandler.handle_success(created_user)
