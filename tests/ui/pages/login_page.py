from playwright.sync_api import Page, Locator

"""封装登录页面的元素定位和打开页面登录操作"""
class LoginPage:
    def __init__(self, page: Page):
        self.page = page

    @property
    def title(self):
        return self.page.get_by_role("heading", name="登录")

    @property
    def username_input(self) -> Locator:
        return self.page.get_by_label("用户名")

    @property
    def password_input(self) -> Locator:
        return self.page.get_by_label("密码")

    @property
    def submit_button(self) -> Locator:
        return self.page.get_by_role("button", name="登录")

    @property
    def error_message(self) -> Locator:
        return self.page.get_by_role("alert")

    def open(self, base_url: str) -> None:
        self.page.goto(base_url)

    def submit_credentials(self, username: str, password: str) -> None:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()