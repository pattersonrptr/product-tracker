import logging

from fastapi import APIRouter, Depends

from src.app.infrastructure.database_config import get_db
from src.app.infrastructure.repositories.user_repository import UserRepository
from src.app.domain.validators.user_validator import UserValidator
from src.app.interfaces.response_handlers.user_response_handler import UserResponseHandler

from src.app.interfaces.schemas.user_schema import (
    UsersCollectionResponse,
    UserResource,
    UserCreateRequest,
    UserReadResponse,
    UserUpdateRequest,
)
from src.app.interfaces.schemas.jsonapi_errors import JsonApiErrorResponse

from src.app.use_cases.user_use_cases import (
    CreateUserUseCase,
    GetUserByIdUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
    GetUserByUsernameUseCase,
    GetUserByEmailUseCase,
    GetAllUsersUseCase,
    pwd_context,
)
from fastapi.responses import JSONResponse

router = APIRouter(tags=["users"], prefix="/users")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_user_repository(db = Depends(get_db)) -> UserRepository:
    """
    TODO: Move to shared module (e.g., src/app/infrastructure/dependencies.py)
    for reuse across multiple routers (auth, register, etc.).
    """
    return UserRepository(db)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


@router.post("/", response_model=UserReadResponse, status_code=201)
def create_user(
    user_in: UserCreateRequest,
    user_repo: UserRepository = Depends(get_user_repository),
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


@router.get("/", response_model=UsersCollectionResponse)
def read_users(
    user_repo: UserRepository = Depends(get_user_repository),
):
    get_all_users_uc = GetAllUsersUseCase(user_repo)
    users_entities = get_all_users_uc.execute()
    data = [UserResource.from_entity(u) for u in users_entities]
    return {"data": data}


@router.get("/username/{username}", response_model=UserReadResponse)
def read_user_by_username(
    username: str,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Returns a user by username in JSON:API format.
    - 200: { "data": { ...resource object... } }
    - 400: { "errors": [ validation ] }
    - 404: { "errors": [ { status, code, title, detail, source } ] }
    """
    validator = UserValidator(user_repo)
    validation_errors = validator.validate_get_by_username_request(username)
    
    if validation_errors:
        return UserResponseHandler.handle_validation_errors(validation_errors)

    get_user_uc = GetUserByUsernameUseCase(user_repo)
    user_entity = get_user_uc.execute(username)
    
    if not user_entity:
        return UserResponseHandler.handle_not_found(f"username '{username}'", "/username")
    
    return UserResponseHandler.handle_success(user_entity)


@router.get("/email/{email}", response_model=UserReadResponse)
def read_user_by_email(
    email: str,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Returns a user by email in JSON:API format.
    - 200: { "data": { ...resource object... } }
    - 400: { "errors": [ validation ] }
    - 404: { "errors": [ { status, code, title, detail, source } ] }
    """
    validator = UserValidator(user_repo)
    validation_errors = validator.validate_get_by_email_request(email)
    
    if validation_errors:
        return UserResponseHandler.handle_validation_errors(validation_errors)

    get_user_uc = GetUserByEmailUseCase(user_repo)
    user_entity = get_user_uc.execute(email)
    
    if not user_entity:
        return UserResponseHandler.handle_not_found(f"email '{email}'", "/email")
    
    return UserResponseHandler.handle_success(user_entity)


@router.get("/{user_id}", response_model=UserReadResponse)
def read_user(
    user_id: int,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Returns a single user in JSON:API format.
    - 200: { "data": { ...resource object... } }
    - 404: { "errors": [ { status, code, title, detail, source } ] }
    """
    get_user_uc = GetUserByIdUseCase(user_repo)
    user_entity = get_user_uc.execute(user_id)
    
    if not user_entity:
        return UserResponseHandler.handle_not_found(f"id {user_id}", "/data/id")
    
    return UserResponseHandler.handle_success(user_entity)


@router.put("/{user_id}", response_model=UserReadResponse)
def update_user(
    user_id: int,
    user_in: UserUpdateRequest,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Updates a user in JSON:API format.
    - 200: { "data": { ...resource object... } }
    - 404: { "errors": [ { status, code, title, detail, source } ] }
    - 409: { "errors": [ duplicate username/email conflict ] }
    - 422: { "errors": [ validation ] }
    """
    validator = UserValidator(user_repo)
    validation_errors = validator.validate_update_request(user_in, user_id)
    
    if validation_errors:
        return UserResponseHandler.handle_validation_errors(validation_errors)

    get_user_uc = GetUserByIdUseCase(user_repo)
    user_entity = get_user_uc.execute(user_id)
    
    if not user_entity:
        return UserResponseHandler.handle_not_found(f"id {user_id}", "/data/id")

    update_uc = UpdateUserUseCase(user_repo)
    updated_user = update_uc.execute(user_id, user_in)
    return UserResponseHandler.handle_success(updated_user)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Deletes a user in JSON:API format.
    - 204: No Content (success, no body)
    - 404: { "errors": [ { status, code, title, detail, source } ] }
    """
    validator = UserValidator(user_repo)
    validation_errors = validator.validate_delete_request(user_id)
    
    if validation_errors:
        return JSONResponse(
            status_code=404,
            content=JsonApiErrorResponse(errors=validation_errors).model_dump(),
            media_type="application/vnd.api+json",
        )

    get_user_uc = GetUserByIdUseCase(user_repo)
    user_entity = get_user_uc.execute(user_id)
    
    if not user_entity:
        return UserResponseHandler.handle_not_found(f"id {user_id}", "/data/id")

    delete_uc = DeleteUserUseCase(user_repo)
    deleted = delete_uc.execute(user_id)
    
    if not deleted:
        return UserResponseHandler.handle_not_found(f"id {user_id}", "/data/id")
    
    return None
