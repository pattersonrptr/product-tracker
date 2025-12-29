from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from src.common.jsonapi import (
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
    is_staff: Optional[bool] = False
    is_superuser: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserAttributesForCreation(BaseModel):
    """Attributes for creation - with password, without timestamps"""
    username: str
    email: EmailStr
    password: str
    is_active: Optional[bool] = True
    is_staff: Optional[bool] = False
    is_superuser: Optional[bool] = False


class UserAttributesForUpdate(BaseModel):
    """Attributes for update - optional fields"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_staff: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserResource(ResourceObject):
    type: str = Field(default="users", examples=["users"])
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
    type: str = Field(default="users", examples=["users"])
    attributes: UserAttributesForCreation


class UserResourceForUpdate(ResourceObjectForCreation):
    """ResourceObject for user update (without id)"""
    type: str = Field(default="users", examples=["users"])
    attributes: UserAttributesForUpdate


class UserCreateRequest(SingleResourceRequest):
    data: UserResourceForCreation


class UserUpdateRequest(SingleResourceRequest):
    data: UserResourceForUpdate


class UserReadResponse(SingleResourceResponse):
    data: UserResource


class UsersCollectionResponse(CollectionResponse):
    data: List[UserResource]
