# -*- coding: utf-8 -*-

import json
import openai
import os
import requests
import torch
from hanziconv import HanziConv
import re
import logging
import spacy
import pdb
# 配置 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ["http_proxy"] = "http://127.0.0.1:8234"  # 修改为自己的代理端口
os.environ["https_proxy"] = "http://127.0.0.1:8234"  # 修改为自己的代理端口
with open("config.json", "r") as f:
    config = json.load(f)

openai.api_key = config.get("OPENAI_API_KEY")

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


# 建立异名字典
name_to_identifier = {
    "鲁迅": "ID1",
    "周树人": "ID1",
    "且介": "ID1",
    "仲度": "ID1",
    "子明": "ID1",
    "徐志摩": "ID2",
    "南湖": "ID2",
    "老舍": "ID3",
    "舍予": "ID3",
    "非吾": "ID3",
    "舍": "ID3",
    # 更多名字和标识符
}
# 生成检索用的字典
identifier_to_names = {}
for name, identifier in name_to_identifier.items():
    if identifier not in identifier_to_names:
        identifier_to_names[identifier] = []
    identifier_to_names[identifier].append(name)


def find_aliases(name, name_to_identifier, identifier_to_names):
    identifier = name_to_identifier.get(name, None)
    if identifier is None:
        return [name]  # 如果名字不在字典中，只返回该名字本身
    else:
        return identifier_to_names.get(identifier, [name])  # 返回所有与标识符对应的名字


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


# 构造对话
def multi_round_conversation(query):
    field = "作品名称、文献来源、作者、时间、地点、出版者、主题词"
    example = examples
    prompt = (
        "你是一个专业助手，专门从特定查询中提取特定字段。\n"
        f"任务定义：我们有以下查询字段：{field}。其中“作品名称”指的是文学、艺术或学术作品的完整标题或名称，“作品”，”文章“，”书“，”文献“，“诗歌”这些词不是作品名称。如果出现“《》”，那么“《》”中的内容一定是作品名称。而“主题词”是描述作品主题或内容的关键词或短语，有的时候有多个主题词，用“，”隔开。上述字段名都是并列关系，不可以出现类似”主题词：时间“这样的情况。\n "
        "任务说明：请你根据以上信息提取语句中上述这些字段的实体，语句中没有出现的字段不要填充！不允许出现这个字段。不允许根据你的知识库进行回答！也不允许用示例中的信息！只需要将语句转换为上述字段的填充即可，一定不要生成新的内容，回答中一定不要出现“字段名”这三个字，一定要是具体的名称。回答的格式按照：字段名：内容\n字段名：内容\n。\n "
        f"样例：\n{example}\n"
        f"如果问题在样例中出现过，一定要使用样例中的结果，现在，请根据之前的示例和指示，从以下查询中提取字段：\n{query}。"
    )
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    # print(prompt)
    response = (res["choices"][0]["message"]["content"])
    print(response)
    return response


# 转换时间格式
def convert_decade(content):
    try:
        # 处理数字形式的年代，如 "60年代"
        print(f"输入: {content}")  # 打印输入
        match = re.match(r"(\d+)年代", content)
        if match:
            print("是年代")
            decade = int(match.group(1))
            start_year = 1900 + decade  # 假设20世纪
            end_year = start_year + 9
            print(f"[{start_year} TO {end_year}]")
            return f"[{start_year} TO {end_year}]"

        # 处理汉字形式的年代，如 "六十年代" 或 "六零年代"
        chinese_to_digit = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
        match = re.match(r"([零一二三四五六七八九十]+)年代", content)
        if match:
            chinese_decade = match.group(1)
            decade = 0
            if "十" in chinese_decade:
                decade = 10 + chinese_to_digit.get(chinese_decade[1], 0) if len(chinese_decade) > 1 else 10
            elif "零" in chinese_decade:
                decade = chinese_to_digit.get(chinese_decade[0], 0) * 10
            else:
                decade = chinese_to_digit.get(chinese_decade, 0) * 10

            start_year = 1900 + decade  # 假设20世纪
            end_year = start_year + 9
            print(f"[{start_year} TO {end_year}]")
            return f"[{start_year} TO {end_year}]"

    except Exception as e:
        logger.error("An error occurred while converting decade: %s", e)
        return content  # 或者其他默认值

    return content


# 汉语年份转为数字
def chinese_to_arabic(chinese_number):
    chinese_digits = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    arabic_number = 0
    unit_positions = [10 ** i for i in range(4)]
    try:
        for i, char in enumerate(reversed(chinese_number)):
            arabic_number += chinese_digits[char] * unit_positions[i]
        return arabic_number
    except Exception as e:
        logger.error(f"在 chinese_to_arabic 函数中出现错误：无法识别的字符 '{e.args[0]}'")
        return None


# 判断逻辑关系词
def set_combines(field, filtered_fields):
    if filtered_fields:
        if field in ("126", "3", "124") and filtered_fields[-1] in ("126", "3", "124"):
            return "AND"
        else:
            return "OR"
    return None


# 重新定义 parse_time 函数，以包含更多的时间格式处理逻辑
def parse_time(content, logger):
    start = 1833
    end = 2022
    current_year = 2023  # 当前年份，可以通过其他方式获取

    try:
        # 处理 "1950年前"、"1950前"、"1950以前"、"1950年以前" 这样的时间格式
        match = re.match(r"(\d+)(年)?(前|以前|之前)", content)
        if match:
            year = int(match.group(1))
            if 1833 <= year <= 2022:
                end = year - 1
            else:
                end = current_year - year
            return start, end

        # 处理 "1947年后"、"1947后"、"1947以后"、"1947年以后" 这样的时间格式
        match = re.match(r"(\d+)(年)?(后|以后|之后)", content)
        if match:
            start = int(match.group(1)) + 1
            return start, end

        # 处理年代
        match = re.match(r"(\d+)年代", content)
        if match:
            decade = int(match.group(1))
            print(match, decade)
            if "之前" in content or "前" in content:
                end = decade
                return start, end
            elif "之后" in content or "后" in content:
                start = decade + 9
                return start, end
            else:
                return decade, decade + 9

        # 处理精确年份
        match = re.match(r"(\d+)年?", content)
        if match:
            year = int(match.group(1))
            return year, year

        # 处理范围式的表达
        match = re.match(r"\[(\d+) TO (\d+)\]", content)
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            return start, end

    except Exception as e:
        logger.error(f"在 parse_time 函数中出现错误：无法识别的字符 '{e.args[0]}'")

    return start, end


def create_json(fields, contents):
    try:
        filtered_fields = []
        filtered_contents = []
        filtered_combines = []
        types = []
        start, end = 1833, 2022
        invalid_work_names = ["作品", "文献", "书", "文章", "杂志", "刊物", "期刊", "书刊", "书籍", "文献资料", "文献记录", "文献记录", "文献内容"]

        for field, content in zip(fields, contents):
            content = content.strip()  # 去除空格
            content = content.replace("（", "").replace("）", "")  # 去除括号
            content = convert_decade(content)

            if content.lower() not in (
                    "无", "null", "不填充", "未知", "未提及", "none", "空", "undefined", "不确定", "没有相关字段出现", "（无）", "（空）"):
                if field == "2" and content in invalid_work_names:
                    continue

                if field == "126":
                    print("时间问题")
                    start, end = parse_time(content, logger)
                    print(start, end)
                    if start is None or end is None:
                        continue
                    continue

                if field == "3":  # "3" 是作者字段

                    aliases = find_aliases(content, name_to_identifier, identifier_to_names)  # 获取所有别名
                    filtered_fields.extend(["3"] * len(aliases))  # 添加与别名数量相同的字段标识
                    filtered_contents.extend(aliases)  # 添加所有别名
                    types.extend(["0"] * len(aliases))  # 为每个别名添加类型标识
                    if len(aliases) > 1:  # 如果有多于一个的别名，添加 "OR" 连接词
                        filtered_combines.extend(["OR"] * (len(aliases) - 1))
                    continue  # 跳过后续逻辑，进入下一次循环

                if field == "141":  # "141" 是主题词字段
                    topics = content.split('，')  # 假设主题词是用逗号分隔的
                    filtered_fields.extend(["141"] * len(topics))  # 添加与主题词数量相同的字段标识
                    filtered_contents.extend(topics)  # 添加所有主题词
                    types.extend(["0"] * len(topics))  # 为每个主题词添加类型标识
                    if len(topics) > 1:  # 如果有多于一个的主题词，添加 "OR" 连接词
                        filtered_combines.extend(["AND"] * (len(topics) - 1))
                    continue  # 跳过后续逻辑，进入下一次循环

                combine = set_combines(field, filtered_fields)
                if combine:
                    filtered_combines.append(combine)

                filtered_fields.append(field.strip())
                filtered_contents.append(content)
                types.append("0")

        # 在循环结束后检查是否只有一个字段（即字段ID为3的作者字段）
        if len(set(filtered_fields)) == 1 and "3" in filtered_fields:
            original_json = {
                "fields": filtered_fields,
                "contents": filtered_contents,
                "combines": filtered_combines,
                "types": types,
                "start": start,
                "end": end
            }
            all_field_json = {
                "fields": ["1"] * len(filtered_contents),
                "contents": filtered_contents,
                "combines": [],
                "types": ["0"] * len(filtered_contents),
                "start": start,
                "end": end
            }

            return original_json, all_field_json

        return {
            "fields": filtered_fields,
            "contents": filtered_contents,
            "combines": filtered_combines,
            "types": types,
            "start": start,
            "end": end
        }, None

    except Exception as e:
        logger.error("在关键字提取阶段出现了一个错误: %s", e)
        return {
            "fields": [],
            "contents": [],
            "combines": [],
            "types": [],
            "start": 1833,
            "end": 2022
        }, None


def final_result(query):
    query_field = multi_round_conversation(query)
    fields, contents = process_model_output(query_field)
    original_json, all_field_json = create_json(fields, contents)
    if original_json == {
        "fields": [],
        "contents": [],
        "combines": [],
        "types": [],
        "start": 1833,
        "end": 2022
    }:
        original_json = {
            "fields": ["1"],
            "contents": [query],
            "combines": [],
            "types": ["0"],
            "start": 1833,
            "end": 2022
        }
    original_json_str = json.dumps(original_json, indent=4, ensure_ascii=False)

    if all_field_json is not None:
        all_field_json_str = json.dumps(all_field_json, indent=4, ensure_ascii=False)
        # print("original_json:")
        # print(json.dumps(original_json, indent=4, ensure_ascii=False))
        # print("all_field_json:")
        # print(json.dumps(all_field_json, indent=4, ensure_ascii=False))
        return original_json_str, all_field_json_str
    else:
        return original_json_str


query = '金庸1940年前的作品有哪些？'
print(final_result(query))
