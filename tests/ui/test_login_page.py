from playwright.sync_api import expect
from tests.ui.pages.login_page import LoginPage

def test_login_page(page, base_url, api_server):
    login_page = LoginPage(page)
    login_page.open(base_url)
    login_page.submit_credentials("tester", "test123")

    user_heading = page.get_by_role("heading", name="用户列表")
    expect(user_heading).to_be_visible()

def test_invalid_login_shows_error(page, base_url, api_server):
    login_page = LoginPage(page)
    login_page.open(base_url)
    login_page.submit_credentials("tester", "test1231")

    expect(login_page.error_message).to_contain_text("用户名或密码错误")

def test_select_user(logged_in_page):
    #查找
    logged_in_page.get_by_label("角色").select_option("admin")
    logged_in_page.get_by_role("button", name="查询").click()

    table = logged_in_page.get_by_role("table", name="用户列表")
    expect(table).to_contain_text("admin")
    expect(table).not_to_contain_text("tester")

def test_select_by_keyword(users_page):
    #返回响应后进行匹配，匹配成功走后面的断言，匹配不成功则直接超时失败，.expect_response()具有网络响应等待功能
    with users_page.page.expect_response(
        lambda response: ("/api/users?" in response.url
        and "keyword=tester" in response.url
        )
    ) as response_info:
        users_page.filter_users(keyword="tester")
    response = response_info.value
    assert response.status == 200

    expect(users_page.rows).to_have_count(1)
    expect(users_page.rows.first).to_contain_text("tester@example.com")

def test_logout(users_page):
    login_page = users_page.logout()

    expect(login_page.title).to_be_visible()
    expect(login_page.error_message).to_contain_text("已退出登录")
    expect(users_page.panel).to_be_hidden()
    expect(users_page.rows).to_have_count(0)


#输入不存在的名字查询
def test_find_invalid_user(logged_in_page):
    logged_in_page.get_by_label("关键词").fill("invalid")
    logged_in_page.get_by_role("button", name="查询").click()

    expect(logged_in_page.get_by_role("status")).to_contain_text("共 0 个用户")
    expect(logged_in_page.locator("#users-body tr")).to_have_count(0)

def test_filter_by_role_and_keyword(logged_in_page):
    logged_in_page.get_by_label("角色").select_option("user")
    logged_in_page.get_by_label("关键词").fill("TEST")
    logged_in_page.get_by_role("button", name="查询").click()

    rows = logged_in_page.locator("#users-body tr")
    expect(rows).to_have_count(1)
    expect(rows.first).to_contain_text("tester")
    expect(rows.first).to_contain_text("测试用户")
    expect(logged_in_page.get_by_role("status")).to_contain_text("共 1 个用户")

"""校验字段为空时阻止提交"""
def test_login_requires_username(page, base_url, api_server):
    login_page = LoginPage(page)
    login_page.open(base_url)
    login_page.submit_credentials("", "test123")
    expect(login_page.username_input).to_be_focused()
    expect(login_page.title).to_be_visible()

