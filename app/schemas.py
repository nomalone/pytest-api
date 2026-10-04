"""接口请求和响应的数据模型。"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    """所有请求模型的公共配置。"""

    model_config = ConfigDict(extra="forbid")


class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"


class HealthResponse(BaseModel):
    status: Literal["ok"]


class LoginRequest(ApiModel):
    username: str = Field(
        min_length=3,
        max_length=20,
        pattern=r"^[A-Za-z][A-Za-z0-9_]*$",
        examples=["tester"],
    )
    password: str = Field(min_length=6, max_length=64, examples=["test123"])


class UserCreate(ApiModel):
    username: str = Field(
        min_length=3,
        max_length=20,
        pattern=r"^[A-Za-z][A-Za-z0-9_]*$",
        examples=["new_user"],
    )
    password: str = Field(min_length=6, max_length=64, examples=["secret123"])
    display_name: str = Field(min_length=1, max_length=50, examples=["新用户"])
    email: str = Field(
        min_length=5,
        max_length=100,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        examples=["new_user@example.com"],
    )
    role: UserRole = UserRole.USER


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    email: str
    role: UserRole


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    user: UserResponse


class ErrorResponse(BaseModel):
    detail: str

