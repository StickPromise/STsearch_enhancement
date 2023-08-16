from flask import Flask, request, jsonify
from STsearch_enhancement3_0 import final_result
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/get_result', methods=['POST'])
def get_result():
    query = request.json.get('query', '')
    result_json_str = final_result(query)
    return jsonify(result=result_json_str)  # 将结果包装在JSON对象中


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

