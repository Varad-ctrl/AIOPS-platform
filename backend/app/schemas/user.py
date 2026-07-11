"""
Pydantic schemas for the User resource.
"""
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = ""


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="viewer", description="admin | devops_engineer | viewer")


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    role: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None
