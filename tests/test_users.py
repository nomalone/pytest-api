import allure
import pytest

from utils.data_loader import load_json_cases

pytestmark = pytest.mark.regression
FILTER_INVALID_CASES = load_json_cases("user_filter_invalid_cases.json")

@allure.feature("用户模块")
class TestUser:
    @allure.title("未登录认证查询被拒绝")
    def test_users_no_login(self, api_client):
        response = api_client.request(
            method="GET",
            path = "/api/users")
        assert response.status_code == 401
        assert response.json() == {"detail": "无效或缺失的访问令牌"}

    @allure.title("登录后查询用户列表成功")
    @pytest.mark.smoke
    def test_users_login(self, authenticated_client):
        response = authenticated_client.request(
            method="GET",
            path="/api/users",)
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        usernames = {user["username"] for user in body["items"]}
        assert usernames == {"admin", "tester"}
        assert all("password" not in user for user in body["items"])

    @allure.title("登录后查询指定用户成功")
    @pytest.mark.smoke
    def test_get_user_success(self, authenticated_client):
        response = authenticated_client.request(
            method="GET",
            path="/api/users/2",)
        assert response.status_code == 200
        body = response.json()
        assert body == {
            "id": 2,
            "username": "tester",
            "display_name": "测试用户",
            "email": "tester@example.com",
            "role": "user"
        }
        assert "password" not in body

    @allure.title("查询不存在的用户")
    def test_get_user_not_found(self, authenticated_client):
        response = authenticated_client.request(
            method="GET",
            path="/api/users/999")
        assert response.status_code == 404
        body = response.json()
        assert body == {"detail": "用户不存在"}

    @allure.title("创建用户成功")
    def test_create_user_success(self, authenticated_client, user_cleanup):
        payload = {
            "username": "wjh",
            "password": "123456789",
            "display_name": "Pytest测试用户",
            "email": "pytest_user@example.com",
            "role": "user"
        }
        response = authenticated_client.request(
            method="POST",
            path="/api/users",
            json=payload,
        )
        assert response.status_code == 201
        body = response.json()
        user_cleanup.append(body["id"])
        assert body["username"] == payload["username"]
        assert body["email"] == payload["email"]
        assert body["role"] == payload["role"]
        assert "password" not in body

    @allure.title("按角色和关键字筛选用户")
    def test_filter_users(self, authenticated_client):
        response = authenticated_client.request(
            method="GET",
            path="/api/users",
            params={"role": "user", "keyword": "TEST"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert [user["username"] for user in body["items"]] == ["tester"]

    @allure.title("无效令牌访问用户列表被拒绝")
    def test_users_invalid_token(self, authenticated_client):
        response = authenticated_client.request(
            method="GET",
            path="/api/users",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "无效或缺失的访问令牌"}
        recovery_response = authenticated_client.request(
            method="GET",
            path="/api/users",
        )
        assert recovery_response.status_code == 200

    @allure.title("无效查询参数: {param_id}")
    @pytest.mark.parametrize("case", FILTER_INVALID_CASES, ids = lambda case: case["id"])
    def test_filter_users_invalid_params(self, authenticated_client, case):
        response = authenticated_client.request(
            method="GET",
            path="/api/users",
            params=case["query_params"],
        )

        assert response.status_code == case["expected_status"]
        errors = response.json()["detail"]
        assert any(error["loc"] == ["query", case["invalid_field"]] for error in errors)
