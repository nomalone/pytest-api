from uuid import uuid4

import pytest
from playwright.sync_api import expect

from tests.ui.pages.login_page import LoginPage
from tests.ui.pages.users_page import UsersPage


def test_user_list_renders_mocked_response(users_page):
    mock_response = {
        "items": [
            {
                "id": 9001,
                "username": "mock-user",
                "display_name": "模拟用户",
                "email": "mock-user@example.com",
                "role": "user",
            }
        ],
        "total": 1,
    }
    #route代表当前被拦截的请求
    def handle_users_request(route):
        # 符合要求自己构造请求返回
        if route.request.method == "GET":
            route.fulfill(json=mock_response)
        else:
            #不进行拦截，正常请求
            route.continue_()

    #注册拦截规则
    users_page.page.route("**/api/users**", handle_users_request)

    users_page.filter_users(keyword="mock-user")
    expect(users_page.rows).to_have_count(1)
    expect(users_page.rows.first).to_contain_text("mock-user")
    expect(users_page.rows.first).to_contain_text("mock-user@example.com")
    expect(users_page.status).to_contain_text("共 1 个用户")

def test_user_list_shows_api_error(users_page):
    mock_response = {
        "detail": "模拟服务异常"
    }

    def handle_users_request(route):
        if route.request.method == "GET":
            route.fulfill(status=500, json=mock_response)
        else:
            route.continue_()

    #注册拦截规则
    users_page.page.route("**/api/users**", handle_users_request)
    #触发拦截请求
    users_page.filter_users(keyword="mock-user")
    expect(users_page.status).to_contain_text("模拟服务异常")

def test_created_user_can_be_found_in_ui(users_page, authenticated_client, user_cleanup):
    """通过接口创建用户后，使用UI测试能够查询到该用户存在,使用uuid的原因生成后缀是防止删除失败导致该用例不可以使用"""

    suffix = uuid4().hex[:8]
    username = f"wjh_{suffix}"
    email = f"pytest_{suffix}@example.com"

    payload = {
        "username": username,
        "password": "123456789",
        "display_name": "Pytest测试用户",
        "email": email,
        "role": "user"
    }
    response = authenticated_client.request(
        method="POST",
        path="/api/users",
        json=payload,
    )
    assert response.status_code == 201
    user_cleanup.append(response.json()["id"])

    users_page.filter_users(keyword="wjh")
    expect(users_page.rows).to_have_count(1)
    expect(users_page.rows.first).to_contain_text(username)
    expect(users_page.rows.first).to_contain_text(email)

@pytest.mark.parametrize(
    "viewport",[{"width": 1280, "height": 800},{"width": 390, "height": 844}],
    ids=["desktop", "mobile"],
)
def test_users_page_is_usable(page, base_url, api_server, viewport):
    # 设置浏览器视口，再打开页面
    page.set_viewport_size(viewport)

    # 使用页面对象登录
    login_page = LoginPage(page)
    login_page.open(base_url)
    login_page.submit_credentials("tester", "test123")

    users_page = UsersPage(page)
    expect(users_page.table).to_be_visible()

    expect(page.get_by_label("关键词")).to_be_visible()
    users_page.filter_users(keyword="tester")

    expect(users_page.rows).to_have_count(1)
    expect(users_page.rows.first).to_contain_text("tester@example.com")

def test_browser_contexts(page, new_context, api_server, base_url):
    login_page1 = LoginPage(page)
    login_page1.open(base_url)
    login_page1.submit_credentials("tester", "test123")

    context2 = new_context()
    page2 = context2.new_page()

    login_page2 = LoginPage(page2)
    login_page2.open(base_url)
    login_page2.submit_credentials("tester", "test123")

    expect(UsersPage(page).table).to_be_visible()
    expect(UsersPage(page2).table).to_be_visible()

    login_page_after_logout = UsersPage(page).logout()
    expect(login_page_after_logout.title).to_be_visible()
    expect(UsersPage(page).panel).to_be_hidden()
    expect(UsersPage(page2).panel).to_be_visible()