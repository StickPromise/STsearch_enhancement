from flask import Flask, request, jsonify
from STsearch_enhancement12_0 import final_result
from flask_cors import CORS
import logging
import json
from datetime import datetime

# 配置 logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)


@app.route('/')
def hello_world():
    return 'Hello, World!'


# 保存所有请求和响应的列表
all_queries_and_responses = []
@app.before_request
def log_request_info():
    print('Headers: %s', request.headers)
    print('Body: %s', request.get_data())

@app.route('/get_result', methods=['POST'])
def get_result():
    query = request.json.get('query', '')
    result_json_str = final_result(query)
    # 创建一个字典以保存当前的请求和响应
    query_and_response = {
        "提问": query,
        "结果": result_json_str
    }

    # 将这个字典追加到 all_queries_and_responses 列表中
    all_queries_and_responses.append(query_and_response)

    # 将这个列表保存到一个 JSON 文件中
    with open('上图检索记录', 'w', encoding='utf-8') as f:
        json.dump(all_queries_and_responses, f, ensure_ascii=False, indent=4)
    # 记录返回值
    logging.info(f"Returning response for query '{query}': {result_json_str}")
    return jsonify(result=result_json_str)  # 将结果包装在JSON对象中


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=50001, debug=False)

