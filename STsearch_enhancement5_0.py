import json
import openai
import os
import requests
import torch
from hanziconv import HanziConv
import re
import logging
import spacy
logging.basicConfig(level=logging.INFO)


os.environ["http_proxy"] = "http://127.0.0.1:8234"     # 修改为自己的代理端口
os.environ["https_proxy"] = "http://127.0.0.1:8234"    # 修改为自己的代理端口

openai.api_key = "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"    # 修改为自己的api_key

# 读取文件中的例子
with open('prompts.txt', 'r', encoding='utf-8') as file:
    examples = file.read()



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

    # 定义有效的字段名列表
    valid_fields = ["作品名称", "文献来源", "作者", "时间", "地点", "出版者", "主题词"]
    field_to_id = {
        "作品名称": "2",
        "文献来源": "6",
        "作者": "3",
        "地点": "124",
        "时间": "126",
        "出版者": "125",
        "主题词": "141"
    }

    for line in response.split('\n'):
        parts = line.split('：')
        for i in range(len(parts) - 1):
            field = parts[i].strip('（）').strip()
            if field in valid_fields:
                field_id = field_to_id[field]
                content = parts[i + 1].strip()
                fields.append(field_id)
                contents.append(content)

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


# 构造多轮对话
def multi_round_conversation(query):
    # 第一轮对话：提供例子
    field = "作品名称、文献来源、作者、时间、地点、出版者、主题词"
    example = examples
    prompt = (
        "你是一个专业助手，专门从特定查询中提取特定字段。\n"
        f"任务定义：我们有以下查询字段：{field}。其中'作品名称'指的是文学、艺术或学术作品的完整标题或名称，包括作品名，文献名，书籍名，诗名，小说名等，如果出现'《》'，那么'《》'中的内容一定是作品名称。而'主题词'是描述作品主题或内容的关键词或短语。上述字段名都是并列关系，不可以出现类似'主题词：时间'这样的情况。\n"
        "任务说明：请你根据以上信息提取语句中上述这些字段的实体，语句中没有出现的字段不要填充！不允许根据你的知识库进行回答！也不允许用示例中的信息！只需要将语句转换为上述字段的填充即可，一定不要生成新的内容，回答中一定不要出现'字段名'这三个字，一定要是具体的名称。回答的格式按照：字段名：内容\n字段名：内容\n。\n"
        f"样例：\n{example}\n"
        f"现在，请根据之前的示例和指示，从以下查询中提取字段：\n{query}"
    )
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    print(prompt)
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
        filtered_combines = []
        start = end = None

        for field, content in zip(fields, contents):
            content = content.strip()
            content = convert_decade(content)  # 转换时间字段
            if content and content.lower() not in ("无", "NULL", "null", "不填充", "未知", "未提及", "Unknown", "None", "空", "Undefined", "不确定", "没有相关字段出现"):
                if field == "126": # 时间字段处理
                    if content.startswith('[') and ' TO ' in content and content.endswith(']'):
                        # 解析时间范围
                        start, end = content.strip('[]').split(' TO ')
                    else:
                        # 单一年份处理
                        start = end = content.replace("年", "")
                    start, end = int(start), int(end)
                else:
                    if filtered_fields and field in ("126", "3", "124") and filtered_fields[-1] in ("126", "3", "124"):
                        filtered_combines.append("AND")
                    elif filtered_fields:
                        filtered_combines.append("OR")
                    filtered_fields.append(field.strip())
                    filtered_contents.append(content)

        types = ["0"] * len(filtered_fields)
        result = {
            "fields": filtered_fields,
            "contents": filtered_contents,
            "combines": filtered_combines,
            "types": types
        }

        if start is not None and end is not None:
            result["start"] = start
            result["end"] = end

        return result


    except Exception as e:
        logging.error(f"An error occurred while creating JSON: {str(e)}")
        # 可以选择抛出自定义异常或返回特定的错误响应
        raise CustomException("An error occurred while processing the request")


def final_result(query):
    query_field = multi_round_conversation(query)
    fields, contents = process_model_output(query_field)
    result_json = create_json(fields, contents)
    if result_json == {
        "fields": [],
        "contents": [],
        "combines": [],
        "types": []
    }:
        result_json = {
                    "fields": ["1"],
                    "contents": [query],
                    "combines": [],
                    "types": ["0"]
                }

    result_json_str = json.dumps(result_json, indent=4, ensure_ascii=False)
    return result_json_str

query = '能帮我找到张恨水40年代的作品吗'
print(final_result(query))




