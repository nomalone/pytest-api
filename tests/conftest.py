import pytest
import requests
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
from clients.api_client import ApiClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]

#判断目标API是否能够正常提供服务
def is_api_running(base_url):
    health_url = f"{base_url.rstrip('/')}/health"
    try:
        response = requests.get(
            health_url,
            timeout=0.5
        )
    except requests.RequestException:
        return False
    return response.status_code == 200


@pytest.fixture(scope="session")
def api_server(base_url):
    if is_api_running(base_url):
        yield
        return

    # 还没有启动服务
    parsed_url = urlparse(base_url)
    host = parsed_url.hostname
    port = parsed_url.port

    if host not in{"127.0.0.1", "localhost"} or port is None :
        pytest.fail(f"目标API不可用，并且不能自动启动远程服务：{base_url}")

    #子进程去启动API服务
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            host,
            "--port",
            str(port),
        ],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    #
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail("本地API进程启动后异常退出")
            if is_api_running(base_url):
                break
            time.sleep(0.1)
        else:#循环跑完，没有执行break进入这里
            pytest.fail("等待本地API启动超时")
        yield #等待所有用例执行完毕
    finally:
        if process.poll() is None:
            process.terminate()

            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)

# 普通客户端，未进行登录请求鉴权
@pytest.fixture(scope="session")
def api_client(base_url, api_server):
    session = ApiClient(base_url)
    yield session
    session.close()

# 登录鉴权
@pytest.fixture(scope="session")
def authenticated_client(base_url, api_server):
    client = ApiClient(base_url)
    response = client.request(
        method="POST",
        path="/api/login",
        json={
            "username": "tester",
            "password": "test123",
        },
    )
    assert response.status_code == 200

    token = response.json()["access_token"]
    client.set_bearer_token(token)

    yield client
    client.close()

@pytest.fixture
def user_cleanup(authenticated_client):
    user_ids = []
    yield user_ids
    for user_id in user_ids:
        response = authenticated_client.request(
            method="DELETE",
            path=f"/api/users/{user_id}",
        )
        assert response.status_code == 204
