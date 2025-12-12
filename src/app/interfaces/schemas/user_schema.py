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
    """Attributes for creation - with password, without timestamps"""
    username: str
    email: EmailStr
    password: str
    is_active: Optional[bool] = True


class UserAttributesForUpdate(BaseModel):
    """Attributes for update - optional fields"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserResource(ResourceObject):
    attributes: UserAttributes

    @classmethod
    def from_entity(cls, entity) -> "UserResource":
        """
        Factory method: converts an entity (pydantic User) to UserResource JSON:API.
        Delegates construction to the generic factory in jsonapi.py.
        Excludes sensitive fields like hashed_password.
        """
        return cls.from_model(
            entity,
            type_name="users",
            attributes_field=UserAttributes,
            exclude=["hashed_password"],
        )


class UserResourceForCreation(ResourceObjectForCreation):
    """ResourceObject for user creation (without id)"""
    attributes: UserAttributesForCreation


class UserResourceForUpdate(ResourceObjectForCreation):
    """ResourceObject for user update (without id)"""
    attributes: UserAttributesForUpdate


class UserCreateRequest(SingleResourceRequest):
    data: UserResourceForCreation


class UserUpdateRequest(SingleResourceRequest):
    data: UserResourceForUpdate


class UserReadResponse(SingleResourceResponse):
    data: UserResource


class UsersCollectionResponse(CollectionResponse):
    data: List[UserResource]
