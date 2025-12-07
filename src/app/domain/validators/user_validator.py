from typing import List

from src.app.interfaces.schemas.jsonapi_errors import JsonApiError, JsonApiErrorResponse
from src.app.interfaces.schemas.user_schema import UserCreateRequest
from src.app.interfaces.repositories.user_repository import UserRepositoryInterface


class UserValidator:
    def __init__(self, user_repo: UserRepositoryInterface):
        self.user_repo = user_repo

    def validate_create_request(self, user_in: UserCreateRequest) -> List[JsonApiError]:
        """
        Valida um request de criação de usuário.
        Retorna lista de erros (vazia se válido).
        """
        errors = []

        # Validação 1: type deve ser "users"
        if user_in.data.type != "users":
            errors.append(
                JsonApiError(
                    status="400",
                    code="INVALID_TYPE",
                    title="Invalid resource type",
                    detail=f"Expected type 'users', got '{user_in.data.type}'",
                    source={"pointer": "/data/type"},
                )
            )

        attrs = user_in.data.attributes

        # Validação 2: username obrigatório
        if not attrs.username or not attrs.username.strip():
            errors.append(
                JsonApiError(
                    status="422",
                    code="MISSING_FIELD",
                    title="Validation error",
                    detail="Field 'username' is required",
                    source={"pointer": "/data/attributes/username"},
                )
            )

        # Validação 3: email obrigatório
        if not attrs.email or not attrs.email.strip():
            errors.append(
                JsonApiError(
                    status="422",
                    code="MISSING_FIELD",
                    title="Validation error",
                    detail="Field 'email' is required",
                    source={"pointer": "/data/attributes/email"},
                )
            )

        # Validação 4: password obrigatória
        if not attrs.password or not attrs.password.strip():
            errors.append(
                JsonApiError(
                    status="422",
                    code="MISSING_FIELD",
                    title="Validation error",
                    detail="Field 'password' is required",
                    source={"pointer": "/data/attributes/password"},
                )
            )

        # Se houver erros de campos obrigatórios, retorna cedo (não valida duplicatas)
        if errors:
            return errors

        # Validação 5: username já existe
        existing_user_username = self.user_repo.get_by_username(attrs.username)
        if existing_user_username:
            errors.append(
                JsonApiError(
                    status="409",
                    code="DUPLICATE_USERNAME",
                    title="Conflict",
                    detail=f"Username '{attrs.username}' is already registered",
                    source={"pointer": "/data/attributes/username"},
                )
            )

        # Validação 6: email já existe
        existing_user_email = self.user_repo.get_by_email(attrs.email)
        if existing_user_email:
            errors.append(
                JsonApiError(
                    status="409",
                    code="DUPLICATE_EMAIL",
                    title="Conflict",
                    detail=f"Email '{attrs.email}' is already registered",
                    source={"pointer": "/data/attributes/email"},
                )
            )

        return errors
