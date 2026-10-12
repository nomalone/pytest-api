from typing import Annotated
from pathlib import Path as FilePath

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Response, Security, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas import (
    ErrorResponse,
    HealthResponse,
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserRole,
)
from app.store import DuplicateUserError, StoredUser, UserStore


app = FastAPI(
    title="Pytest API Demo",
    description="供 pytest 接口自动化学习使用的本地用户管理 API。",
    version="1.0.0",
    openapi_tags=[
        {"name": "system", "description": "服务状态接口"},
        {"name": "auth", "description": "登录认证接口"},
        {"name": "users", "description": "用户管理接口"},
    ],
)
store = UserStore()
bearer_scheme = HTTPBearer(auto_error=False)


@app.get("/", include_in_schema=False)
def web_home() -> FileResponse:
    """返回 UI 自动化练习用的用户管理页面。"""
    page_path = FilePath(__file__).parent / "static" / "index.html"
    return FileResponse(page_path)


def to_user_response(user: StoredUser) -> UserResponse:
    """把内部用户记录转换成不含密码的接口响应。"""
    return UserResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
    )


def require_authenticated_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_scheme),
    ],
) -> StoredUser:
    """校验 Demo Bearer Token，并返回对应用户。"""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效或缺失的访问令牌",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    token_prefix = "demo-token-"
    if not credentials.credentials.startswith(token_prefix):
        raise unauthorized

    user_id_text = credentials.credentials.removeprefix(token_prefix)
    if not user_id_text.isdigit():
        raise unauthorized

    user = store.get_user(int(user_id_text))
    if user is None:
        raise unauthorized
    return user


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="健康检查",
)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post(
    "/api/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse, "description": "用户名或密码错误"}},
    tags=["auth"],
    summary="用户登录",
)
def login(payload: LoginRequest) -> LoginResponse:
    user = store.authenticate(payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return LoginResponse(
        access_token=f"demo-token-{user.id}",
        token_type="bearer",
        user=to_user_response(user),
    )


@app.get(
    "/api/users",
    response_model=UserListResponse,
    dependencies=[Depends(require_authenticated_user)],
    responses={401: {"model": ErrorResponse, "description": "访问令牌无效或缺失"}},
    tags=["users"],
    summary="查询用户列表",
)
def list_users(
    role: Annotated[UserRole | None, Query(description="按角色筛选用户")] = None,
    keyword: Annotated[
        str | None,
        Query(min_length=1, max_length=50, description="按用户名、显示名称或邮箱搜索"),
    ] = None,
) -> UserListResponse:
    users = [to_user_response(user) for user in store.list_users(role, keyword)]
    return UserListResponse(items=users, total=len(users))


@app.get(
    "/api/users/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_authenticated_user)],
    responses={
        401: {"model": ErrorResponse, "description": "访问令牌无效或缺失"},
        404: {"model": ErrorResponse, "description": "用户不存在"},
    },
    tags=["users"],
    summary="根据 ID 查询用户",
)
def get_user(
    user_id: Annotated[int, Path(gt=0, description="用户 ID")],
) -> UserResponse:
    user = store.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return to_user_response(user)


@app.post(
    "/api/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_authenticated_user)],
    responses={
        401: {"model": ErrorResponse, "description": "访问令牌无效或缺失"},
        409: {"model": ErrorResponse, "description": "用户名或邮箱重复"},
    },
    tags=["users"],
    summary="创建用户",
)
def create_user(payload: UserCreate) -> UserResponse:
    try:
        user = store.create_user(payload)
    except DuplicateUserError as error:
        message = "用户名已存在" if error.field == "username" else "邮箱已存在"
        raise HTTPException(status_code=409, detail=message) from error
    return to_user_response(user)


@app.delete(
    "/api/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_authenticated_user)],
    responses={
        401: {"model": ErrorResponse, "description": "访问令牌无效或缺失"},
        404: {"model": ErrorResponse, "description": "用户不存在"},
    },
    tags=["users"],
    summary="删除用户",
)
def delete_user(
    user_id: Annotated[int, Path(gt=0, description="用户 ID")],
) -> Response:
    if not store.delete_user(user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
