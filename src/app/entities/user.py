from datetime import datetime

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int | None = None
    username: str
    email: EmailStr
    hashed_password: str | None = None
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
