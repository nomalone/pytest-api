# Pytest API Demo 接口文档

## 1. 服务信息

- 服务地址：`http://127.0.0.1:8000`
- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`
- OpenAPI JSON：`http://127.0.0.1:8000/openapi.json`
- 请求和响应格式：`application/json`

启动命令：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

服务使用内存存储。服务重启后，新建和删除的数据会恢复到初始状态。密码和令牌逻辑仅用于自动化测试练习，不适用于生产环境。

除健康检查和登录外，用户管理接口都需要请求头：

```http
Authorization: Bearer demo-token-2
```

令牌缺失或无效时返回 `401 Unauthorized`：

```json
{
  "detail": "无效或缺失的访问令牌"
}
```

## 2. 初始账号

| 用户名 | 密码 | 角色 | 用户 ID |
|---|---|---|---:|
| `admin` | `admin123` | `admin` | 1 |
| `tester` | `test123` | `user` | 2 |

## 3. 健康检查

### `GET /health`

成功响应：`200 OK`

```json
{
  "status": "ok"
}
```

## 4. 用户登录

### `POST /api/login`

请求体：

```json
{
  "username": "tester",
  "password": "test123"
}
```

登录成功：`200 OK`

```json
{
  "access_token": "demo-token-2",
  "token_type": "bearer",
  "user": {
    "id": 2,
    "username": "tester",
    "display_name": "测试用户",
    "email": "tester@example.com",
    "role": "user"
  }
}
```

账号或密码错误：`401 Unauthorized`

```json
{
  "detail": "用户名或密码错误"
}
```

## 5. 查询用户列表

### `GET /api/users`

需要 Bearer Token。

可选查询参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `role` | `admin` 或 `user` | 按角色筛选 |
| `keyword` | 1～50 个字符 | 按用户名、显示名称或邮箱搜索，不区分大小写 |

示例：`GET /api/users?role=user`

参数可以组合使用，例如：`GET /api/users?role=user&keyword=TEST`

成功响应：`200 OK`

```json
{
  "items": [
    {
      "id": 2,
      "username": "tester",
      "display_name": "测试用户",
      "email": "tester@example.com",
      "role": "user"
    }
  ],
  "total": 1
}
```

## 6. 查询单个用户

### `GET /api/users/{user_id}`

需要 Bearer Token。

用户存在时返回：`200 OK` 和用户对象。例如请求 `GET /api/users/2`：

```json
{
  "id": 2,
  "username": "tester",
  "display_name": "测试用户",
  "email": "tester@example.com",
  "role": "user"
}
```

响应不会包含用户密码。

用户不存在：`404 Not Found`

```json
{
  "detail": "用户不存在"
}
```

`user_id` 必须大于 0，否则 FastAPI 返回 `422 Unprocessable Entity`。

## 7. 创建用户

### `POST /api/users`

需要 Bearer Token。

请求体：

```json
{
  "username": "new_user",
  "password": "secret123",
  "display_name": "新用户",
  "email": "new_user@example.com",
  "role": "user"
}
```

字段规则：

| 字段 | 必填 | 规则 |
|---|---|---|
| `username` | 是 | 3～20 个字符；字母开头；只能包含字母、数字和下划线 |
| `password` | 是 | 6～64 个字符 |
| `display_name` | 是 | 1～50 个字符 |
| `email` | 是 | 符合基本邮箱格式，最长 100 个字符 |
| `role` | 否 | `admin` 或 `user`，默认 `user` |

创建成功：`201 Created`，响应不包含密码。

用户名重复：`409 Conflict`

```json
{
  "detail": "用户名已存在"
}
```

邮箱重复：`409 Conflict`

```json
{
  "detail": "邮箱已存在"
}
```

请求字段缺失、格式错误或包含未定义字段时，返回 `422 Unprocessable Entity`。

## 8. 删除用户

### `DELETE /api/users/{user_id}`

需要 Bearer Token。

- 删除成功：`204 No Content`，响应体为空。
- 用户不存在：`404 Not Found`。
- `user_id` 不大于 0：`422 Unprocessable Entity`。

删除接口主要用于后续自动化测试清理自己创建的数据。

## 9. 通用错误格式

业务错误使用：

```json
{
  "detail": "错误说明"
}
```

参数校验失败时，FastAPI 返回 `422`，`detail` 是包含字段位置、错误类型和说明的数组。后续 pytest 用例会分别验证业务错误和参数校验错误。
