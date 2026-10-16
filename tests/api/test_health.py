import pytest
import allure

@pytest.mark.smoke
@pytest.mark.regression
@allure.feature("系统状态")
@allure.title("服务健康检查成功")
def test_health(api_client):
    response = api_client.request(
        method="GET",
        path="/health"
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
