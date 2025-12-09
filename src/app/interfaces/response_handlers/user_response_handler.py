from fastapi.responses import JSONResponse

from src.app.interfaces.schemas.jsonapi_errors import JsonApiError, JsonApiErrorResponse
from src.app.interfaces.schemas.user_schema import UserReadResponse, UserResource
from src.app.entities.user import User as UserEntity


class UserResponseHandler:
    """
    Centraliza respostas JSON:API para users.
    Responsável por transformar entidades em respostas padronizadas.
    """

    @staticmethod
    def handle_validation_errors(validation_errors: list) -> JSONResponse:
        """
        Retorna erros de validação em formato JSON:API.
        """
        first_error = validation_errors[0]
        status_code = int(first_error.status)
        return JSONResponse(
            status_code=status_code,
            content=JsonApiErrorResponse(errors=validation_errors).model_dump(),
            media_type="application/vnd.api+json",
        )

    @staticmethod
    def handle_not_found(identifier: str, pointer: str) -> JSONResponse:
        """
        Retorna 404 em formato JSON:API.
        """
        errors = [
            JsonApiError(
                status="404",
                code="NOT_FOUND",
                title="User not found",
                detail=f"User with {identifier} not found",
                source={"pointer": pointer},
            )
        ]
        return JSONResponse(
            status_code=404,
            content=JsonApiErrorResponse(errors=errors).model_dump(),
            media_type="application/vnd.api+json",
        )

    @staticmethod
    def handle_success(entity: UserEntity) -> UserReadResponse:
        """
        Retorna usuário em formato JSON:API (sucesso).
        """
        return UserReadResponse(data=UserResource.from_entity(entity))
