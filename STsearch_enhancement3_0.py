import json
import openai
import os
import requests
import torch
from hanziconv import HanziConv
import re
import logging

logging.basicConfig(level=logging.INFO)


os.environ["http_proxy"] = "http://127.0.0.1:8234"     # 修改为自己的代理端口
os.environ["https_proxy"] = "http://127.0.0.1:8234"    # 修改为自己的代理端口

openai.api_key = "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"    # 修改为自己的api_key


# 调用7b模型
def ask_solo_7b(text, loratype):
    url_7b = 'http://10.176.64.118:50003'
    response = requests.post(f'{url_7b}/ans', json={'query': text, 'loratype': loratype}).json()
    ans = response['ans']
    suc = response['success']
    if not suc: return ans
    print('CuteGPT')
    print(f">>>>>>>>>>>>\n{text}\n{ans}\n<<<<<<<<<<<<<\n")

    return ans


# 调用13b模型
def get_ans(prompt):
    # 根据历史对话，cute gpt得到答案
    response = requests.post("http://10.176.40.138:23489/ddemos/cutegpt_normal/run/submit", json={
        "data": [
            prompt,
            [],
            None,
        ]
    }).json()
    return response["data"][0][0][1]

# 按照：匹配出需要的字段，并且转换为id
def process_model_output(response):
    fields = []
    contents = []
    lines = response.split('\n')
    field_to_id = {
        "文献名": "2",
        "文献来源": "6",
        "作者": "3",
        "近代期刊-出版地": "124",
        "近代图书-出版时间": "126",
        "近代图书-出版者": "125",
        "近代图书-主题词": "141"
    }

    for line in lines:
        if '：' in line:
            field, content = line.split('：')
            field = field.strip('（）')  # 新增这行，去掉字段名中的括号
            field_id = field_to_id.get(field, "")
            if field_id:
                fields.append(field_id)
                contents.append(content.strip())
    return fields, contents


def get_ans(prompt):

    # 根据历史对话，cute gpt得到答案
    response = requests.post("http://10.176.40.138:23489/ddemos/cutegpt_normal/run/submit", json={
        "data": [
            prompt,
            [],
            None,
        ]
    }).json()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print(response)
    return response["data"][0][0][1]


# 告诉模型有什么字段和含义，获得加工后的prompt
def process_query(query):
    # 提供上下文信息
    example = "作者：鲁迅\n近代图书-出版时间：[1930 TO 1940]\n近代图书-出版地：北平\n近代图书-主题词：社会文学\n"
    field = "（文献名）、（文献来源）、（作者）、（近代图书-出版时间）、（近代图书-出版地）、（近代图书-出版者）、（近代图书-主题词）"
    example3 = "AND,\nOR"
    rest = '并输出语句中的查询字段间的逻辑关系（AND、OR、NOT），只按顺序返回给我这几个查询字段的逻辑关系即可，如：{example3}, 逻辑关系的数量是查询字段的数量 - 1'
    prompt = f"我们有以下查询字段：\n{field}。 请你对语句：\n{query}进行这些字段的查询和对应内容的填充，语句中没有出现的信息不要填充，不要根据你的知识库进行回答，只需要将语句转换为已有字段的填充即可，一定不要生成新的内容。回答的格式按照下面的即可：字段名：内容\n字段名：内容\n。下面是一个例子：\n query:请找出鲁迅在1930年到1940年在北平写的有关社会文学的作品。\n你的回答应该是：{example}。"
    return prompt

# 获得答案
def get_query_field(prompt):
    # # 调用Cute gpt
    # response = get_ans(prompt)
    # print(response)
    # 提供上下文信息
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}  # 单轮对话，修改其中的content
        ]
    )

    response = (res["choices"][0]["message"]["content"])
    return response

# 转换时间格式
def convert_decade(content):
    match = re.match(r"(\d+)年代", content)
    if match:
        decade = int(match.group(1))
        start_year = 1900 + decade
        end_year = start_year + 9
        return f"[{start_year} TO {end_year}]"
    return content


def create_json(fields, contents):
    try:
        filtered_fields = []
        filtered_contents = []
        for field, content in zip(fields, contents):
            content = content.strip()
            content = convert_decade(content)  # 转换时间字段
            if content and content != "无":
                filtered_fields.append(field.strip())
                filtered_contents.append(content)
        combines = ["AND"] * (len(filtered_fields) - 1)
        types = ["0"] * len(filtered_fields)
        result = {
            "fields": filtered_fields,
            "contents": filtered_contents,
            "combines": combines,
            "types": types
        }
        return result
    except Exception as e:
        logging.error(f"An error occurred while creating JSON: {str(e)}")
        # 可以选择抛出自定义异常或返回特定的错误响应
        raise CustomException("An error occurred while processing the request")


def final_result(query):
    processed_query = process_query(query)
    query_field = get_query_field(processed_query)
    fields, contents = process_model_output(query_field)
    result_json = create_json(fields, contents)
    result_json_str = json.dumps(result_json, indent=4, ensure_ascii=False)
    return result_json_str

query = '有没有胡适在60年代写的文章？'
print(final_result(query))




