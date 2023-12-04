import uuid
from typing import Any, Dict, Optional

from fastapi_users import schemas
from pydantic import BaseModel, Json


class BaseRole(BaseModel):
    id: int
    name: str
    permissions: dict[str, Any] | None

    class Config:
        from_attributes = True


class RoleRead(BaseRole):
    pass


class UserRead(schemas.BaseUser[uuid.UUID]):
    role: RoleRead
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass
