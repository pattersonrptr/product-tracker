from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr

from src.app.interfaces.schemas.jsonapi import (
    ResourceObject,
    ResourceObjectForCreation,
    SingleResourceRequest,
    SingleResourceResponse,
    CollectionResponse,
)

class UserAttributes(BaseModel):
    username: str
    email: EmailStr
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserAttributesForCreation(BaseModel):
    """Attributes para criação - com password, sem timestamps"""
    username: str
    email: EmailStr
    password: str
    is_active: Optional[bool] = True


class UserResource(ResourceObject):
    attributes: UserAttributes

    @classmethod
    def from_entity(cls, entity) -> "UserResource":
        """
        Factory method: converte uma entidade (pydantic User) em UserResource JSON:API.
        Delega a construção para a fábrica genérica em jsonapi.py.
        Exclui campos sensíveis como hashed_password.
        """
        return cls.from_model(
            entity,
            type_name="users",
            attributes_field=UserAttributes,
            exclude=["hashed_password"],
        )


class UserResourceForCreation(ResourceObjectForCreation):
    """ResourceObject para criação de users (sem id)"""
    attributes: UserAttributesForCreation


class UserCreateRequest(SingleResourceRequest):
    data: UserResourceForCreation


class UserReadResponse(SingleResourceResponse):
    data: UserResource


class UsersCollectionResponse(CollectionResponse):
    data: List[UserResource]
