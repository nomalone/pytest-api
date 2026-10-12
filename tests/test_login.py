import pytest
import allure
from utils.data_loader import load_json_cases

#这个模块下的所有用例都属于regression
pytestmark = pytest.mark.regression
LOGIN_INVALID_CASES = {case["id"]: case for case in load_json_cases("login_invalid_cases.json")}

@allure.feature("登录模块")
class TestLogin:
    @allure.title("登陆成功")
    @pytest.mark.smoke
    def test_login_success(self,  api_client):
        payload = {
            "username": "tester",
            "password": "test123"
        }
        response = api_client.request(
            method="POST",
            path="/api/login",
            json=payload,
        )

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["access_token"], str)
        assert body["access_token"]
        assert "password" not in body["user"]
        assert body['token_type'] == 'bearer'
        assert body['user']['username'] == 'tester'
        assert body['user']['id'] == 2

    @allure.title("错误的密码/账号：{param_id}")
    @pytest.mark.parametrize(
        "case_id",
        LOGIN_INVALID_CASES.keys(),
    )
    def test_login_invalid_credentials(self, api_client, case_id):
        case = LOGIN_INVALID_CASES[case_id]
        response = api_client.request(
            method="POST",
            path="/api/login",
            json=case["request_body"],
        )
        assert response.status_code == case["expected_status"]
        assert response.json() == case["expected_body"]

