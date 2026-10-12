import pytest
from playwright.sync_api import expect
from tests.ui.pages.login_page import LoginPage
from tests.ui.pages.users_page import UsersPage

@pytest.fixture
def logged_in_page(page, base_url, api_server):
    login_page = LoginPage(page)
    login_page.open(base_url)
    login_page.submit_credentials("tester", "test123")
    expect(page.get_by_role("heading", name="用户列表")).to_be_visible()
    expect(page.get_by_role("status")).to_contain_text("共")
    return page

@pytest.fixture
def users_page(logged_in_page):
    return UsersPage(logged_in_page)