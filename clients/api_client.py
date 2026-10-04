import requests
import allure
import json

SENSITIVE_KEYS = {
    "password",
    "access_token",
    "refresh_token",
    "authorization"
}

#通过递归检查是否有敏感字段
def mask_sensitive_data(value):
    if isinstance(value, dict):
        result = {}

        for key, item in value.items():
            if key.lower() in SENSITIVE_KEYS:
                result[key] = "******"
            else:
                result[key] = mask_sensitive_data(item)
        return result

    if isinstance(value, list):
        result = []
        for item in value:
            result.append(mask_sensitive_data(item))
        return result

    return value

class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def request(self, method, path, **kwargs):
        url = f"{self.base_url}/{path.lstrip('/')}"
        kwargs.setdefault("timeout", 3)
        #上下文管理器
        with allure.step(f"{method.upper()} {path}"):
            request_body = kwargs.get("json")
            #下面这一步只是在allure文件中放入脱敏后的请求体
            if request_body is not None:
                safe_request_body = mask_sensitive_data(request_body)
                allure.attach(
                    json.dumps(safe_request_body, ensure_ascii=False, indent=2),
                    name="请求体",
                    attachment_type=allure.attachment_type.JSON,
                )

            #在allure中显示查询参数
            query_params = kwargs.get("params")
            if query_params is not None:
                safe_query_params = mask_sensitive_data(query_params)
                allure.attach(json.dumps(safe_query_params, ensure_ascii=False, indent=2),name="查询参数", attachment_type=allure.attachment_type.JSON)


            response = self.session.request(method, url, **kwargs)
            allure.attach(str(response.status_code),
                          name="响应状态码",
                          attachment_type=allure.attachment_type.TEXT)

            #响应体附件,如果是204此类无响应体的，解析失败后使用response.text
            if response.content:
                try:
                    response_body = response.json()
                except ValueError:
                    response_body = response.text

                safe_response_body = mask_sensitive_data(response_body)
                #只要是dict/list格式都可以
                if isinstance(safe_response_body,(dict,list)):
                    response_text = json.dumps(safe_response_body, ensure_ascii=False, indent=2)
                    response_type = allure.attachment_type.JSON
                else:
                    response_text = str(safe_response_body)
                    response_type = allure.attachment_type.TEXT
                allure.attach(response_text,name="响应体", attachment_type=response_type)
        return response

    def set_bearer_token(self, token):
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def close(self):
        self.session.close()
