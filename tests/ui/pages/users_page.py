from playwright.sync_api import Page, Locator

from tests.ui.pages.login_page import LoginPage


class UsersPage:
    def __init__(self, page: Page):
        self.page = page

    @property
    def table(self) -> Locator:
        return self.page.get_by_role("table", name="用户列表")

    @property
    def rows(self) -> Locator:
        return self.page.locator("#users-body tr")

    @property
    def status(self) -> Locator:
        return self.page.get_by_role("status")

    #可用来验证退出登录后用户区域是否显示
    @property
    def panel(self):
        return self.page.locator("#users-panel")

    def filter_users(self, role=None, keyword=None):
        if role is not None:
            self.page.get_by_label("角色").select_option(role)
        if keyword is not None:
            self.page.get_by_label("关键词").fill(keyword)
        self.page.get_by_role("button", name="查询").click()

    def logout(self):
        self.page.get_by_role("button", name="退出登录").click()
        return LoginPage(self.page)