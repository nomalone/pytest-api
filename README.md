# Pytest API Demo

这是一个用于学习 pytest 接口自动化的完整小型 Demo。项目包含本地 FastAPI 用户管理接口、pytest 测试、请求客户端、JSON 测试数据，以及 Allure 报告。

Demo 已覆盖 pytest 接口测试的主要工作流程和常用语法。它适合学习和本地练习，不是生产级测试平台。

## 环境要求

- Python 3.10 或更高版本
- Java：Allure CLI 运行所需
- Allure Commandline：生成 HTML 报告

Python 依赖列在 `requirements.txt`。`allure-pytest` 插件负责将测试结果写入 `allure-results`；Allure CLI 再把这些结果生成 HTML。

在项目根目录使用 PowerShell 创建虚拟环境并安装依赖：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

确认 Allure CLI 和 Java 可用：

```powershell
allure --version
java -version
```

## 运行测试

### 一条命令运行测试并生成报告

推荐通过项目脚本运行。它会把测试选择和 API 地址传给 pytest；测试期间，`api_server` fixture 会复用已运行的本地 API，或在本地自动启动 API。测试完成后，如果是 fixture 启动的进程，它会负责关闭。

```powershell
# 所有测试，默认选项
.\.venv\Scripts\python.exe scripts\run_tests.py

# 只运行冒烟测试
.\.venv\Scripts\python.exe scripts\run_tests.py --suite smoke

# 运行完整回归测试
.\.venv\Scripts\python.exe scripts\run_tests.py --suite regression

# 指定另一个 API 地址
.\.venv\Scripts\python.exe scripts\run_tests.py --suite smoke --base-url http://127.0.0.1:9000
```

`--suite` 可选值为 `all`、`smoke`、`regression`，默认是 `all`。`--base-url` 默认是 `http://127.0.0.1:8000`。

脚本会先运行 pytest，再调用 Allure CLI 生成 `allure-report`。测试失败时仍会尝试生成报告，并让脚本以 pytest 的失败状态码退出；测试通过时，脚本使用报告生成过程的状态码退出。

### 直接运行 pytest

也可以绕过 `scripts/run_tests.py` 直接运行 pytest：

```powershell
# 所有用例
.\.venv\Scripts\python.exe -m pytest

# 按 marker 选择用例
.\.venv\Scripts\python.exe -m pytest -m smoke
.\.venv\Scripts\python.exe -m pytest -m regression

# 指定 API 地址
.\.venv\Scripts\python.exe -m pytest --base-url http://127.0.0.1:9000
```

直接运行 pytest 会产生 Allure 原始结果，但不会自动生成 HTML。需要时再执行：

```powershell
allure generate allure-results -o allure-report --clean
```

生成后可用浏览器打开 `allure-report/index.html`。也可以通过 Allure CLI 启动本地报告服务：

```powershell
allure open allure-report
```

## API 文档

本地 API 地址默认为 `http://127.0.0.1:8000`。接口列表、请求字段和响应示例见 [接口文档](docs/API.md)。

手动启动 API 的命令：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

启动后可以访问：

- Swagger UI：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>

API 使用内存存储，服务重启后会恢复初始数据。Demo 的账号、密码和 Token 仅用于本地测试练习。

## 项目结构

```text
app/                    FastAPI Demo 接口和内存用户仓库
clients/                requests 会话封装与 Allure 请求/响应附件
docs/API.md             API 接口说明
scripts/run_tests.py    测试集选择、pytest 调用、Allure HTML 生成
tests/                  pytest 测试、fixtures 和 JSON 测试数据
tests/data/             参数化用例使用的 JSON 文件
utils/data_loader.py    JSON 测试数据加载与基本结构校验
pytest.ini              pytest 收集、缓存、marker 和 Allure 配置
requirements.txt        Python 依赖
```

## Demo 覆盖的 pytest 用法

### 测试发现和断言

pytest 默认发现 `test_*.py` 文件中的 `test_*` 函数，执行 Python `assert`：

```python
assert response.status_code == 200
assert response.json() == {"status": "ok"}
```

断言失败时，pytest 会展示实际表达式和值。

### Fixture、依赖和清理

测试函数把 fixture 名称写成参数，pytest 会按名称注入它：

```python
def test_users_login(authenticated_client):
    ...
```

`authenticated_client` 依赖 `base_url` 和 `api_server`；fixture 也可以依赖其他 fixture。`scope="session"` 表示同一 pytest 会话内共享实例。普通 `@pytest.fixture` 默认是 `function` 作用域，每个测试函数各运行一次。

`yield` fixture 在 `yield` 之前做准备，在测试使用完 fixture 后执行后续清理：

```python
@pytest.fixture
def user_cleanup(authenticated_client):
    created_ids = []
    yield created_ids
    # 测试结束后删除本测试创建的用户
```

`api_server` 使用相同的准备/清理模式启动和关闭本地 API 子进程。若 API 已经运行，fixture 会复用它，不会关闭外部启动的服务。

### 装饰器和动态 Allure 标题

以 `@` 开头的写法是装饰器。pytest 和 Allure 用装饰器给测试函数增加能力或报告信息：

```python
@pytest.mark.smoke
@allure.feature("用户模块")
@allure.title("无效查询参数：{param_id}")
```

`@pytest.mark.parametrize(...)` 会让 pytest 为每组数据生成一个测试实例；`ids=` 提供节点 ID，`{param_id}` 可以把该 ID 放进 Allure 标题。例如报告标题可以显示为“无效查询参数：invalid-role”。装饰器本身不是 pytest 测试函数里的语句，而是在定义函数时附加行为或元信息。

### 自定义命令行参数和 pytest 钩子

`pytest_addoption(parser)` 是 pytest 会自动调用的钩子函数。`parser.addoption()` 注册 `--base-url`，`pytestconfig.getoption()` 读取实际值。通过 `run_tests.py` 时，脚本把参数转交给 pytest；直接运行 pytest 时则使用 `conftest.py` 里的默认值。

### Marker：分组和选择用例

`pytest.ini` 注册了 `smoke` 和 `regression` marker。用 `@pytest.mark.smoke` 给测试打标签，再用 `pytest -m smoke` 选择该组。文件级的：

```python
pytestmark = pytest.mark.regression
```

表示该测试模块中的用例都带有 `regression` 标记。

### 参数化与 JSON 外部数据

`@pytest.mark.parametrize()` 把一份测试函数运行多次。简单数据可直接写在装饰器中；本项目将登录失败和非法查询参数放在 JSON 文件中：

```python
cases = load_json_cases("user_filter_invalid_cases.json")

@pytest.mark.parametrize("case", cases, ids=lambda case: case["id"])
def test_filter_users_invalid_params(authenticated_client, case):
    ...
```

`ids=` 为每组数据指定 pytest 节点 ID，例如 `invalid-role`。数据加载器用 `json.load()` 将 JSON 数组变成 Python 列表、对象变成字典，并检查每条数据是否有唯一的 `id`。

登录失败用例通过 `case_id` 查找数据，而不是把包含密码的整份字典交给 pytest 参数，避免敏感值出现在 Allure 参数信息里。

### Python 语法：`**kwargs`、推导式和递归

`ApiClient.request(method, path, **kwargs)` 用 `**kwargs` 接收可变关键字参数，因此同一个请求方法可以适配：

```python
client.request("GET", "/api/users", params={"role": "user"})
client.request("POST", "/api/users", json=payload)
client.request("GET", "/api/users", headers={"Authorization": "Bearer ..."})
```

列表推导式：

```python
[user["username"] for user in body["items"]]
```

会从用户对象列表中提取用户名。生成器表达式配合 `any()` 可判断一组错误中是否包含指定字段：

```python
any(error["loc"] == ["query", "role"] for error in errors)
```

`mask_sensitive_data()` 用递归处理嵌套字典和列表，将密码、Token 等字段替换为 `******`，用于安全地生成 Allure 附件。

数据加载器还使用了这些 Python 语法：

- `with file_path.open(...) as file:` 是上下文管理器，代码块结束后自动关闭文件。
- `json.load(file)` 从文件读取 JSON；`json.loads(text)` 则从字符串解析 JSON。
- `list[dict]` 是类型标注，说明函数预期返回“由字典组成的列表”；它不会在运行时自动校验数据。
- `str | None` 表示值可以是字符串或 `None`，是 Python 3.10 起支持的联合类型写法。
- `enumerate(cases, start=1)` 遍历数据时同时取得序号和值；`set()` 用来记录已见 ID 并检查重复。
- `{case["id"]: case for case in cases}` 是字典推导式，用测试 ID 查找对应的完整数据。

API 自动启动 fixture 还用到 `try/finally` 和 `subprocess.Popen()`：`try/finally` 保证测试结束时执行进程清理；`Popen()` 启动一个持续运行的 Uvicorn 子进程，`poll()` 检查进程状态，`terminate()` 请求退出，`wait()` 等待退出完成。

### Allure 步骤和附件

`with allure.step(...)` 将一次 HTTP 请求显示成报告步骤。`allure.attach(...)` 将脱敏后的请求体、查询参数、响应状态码和响应体作为步骤附件。请求实际发送的仍是原始数据，脱敏副本只用于报告。

## 当前测试覆盖

当前有 13 个测试实例，覆盖健康检查、登录成功/失败、用户查询/创建、认证、查询筛选和参数校验。可用 `smoke` 快速检查核心成功链路，用 `regression` 运行全量测试。

项目持续学习还可以继续扩展 `skip` / `xfail`、`pytest.raises`、`monkeypatch` 等内容；它们不是当前接口自动化主链路运行的前提。
