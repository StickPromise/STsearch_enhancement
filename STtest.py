import requests
import json

# 服务器的URL
url = "http://127.0.0.1:50001/get_result"

# 您要查询的内容
query = "请帮我找到鲁迅1944年有关抗战的书籍"

# 创建请求的JSON数据
data = {
    "query": query
}

# 发送POST请求
response = requests.post(url, json=data)

# 检查响应状态
if response.status_code == 200:
    result_json_str = response.json().get('result', '')
    print("接收到的JSON结果：")
    print(result_json_str)
else:
    print(f"请求失败，状态码：{response.status_code}")

