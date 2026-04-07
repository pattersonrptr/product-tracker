from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    username: str
    email: EmailStr
    hashed_password: str | None = None
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
