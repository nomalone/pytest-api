from playwright.sync_api import expect

def test_home_page_title(page, base_url, api_server):
    page.goto(base_url)

    heading = page.get_by_role("heading", name="用户管理")
    expect(heading).to_be_visible()
