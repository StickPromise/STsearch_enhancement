from langchain.document_loaders import DirectoryLoader
import jieba
import jieba.posseg as pseg
from langchain.text_splitter import CharacterTextSplitter
import numpy as np
import os
import json
from rank_bm25 import BM25Okapi
import dateparser
from dateparser import search
from fuzzywuzzy import fuzz
import torch
import openai
import os
import requests

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
        if '：' in line: # 如果 line 中包含分隔符
            field, content = line.split('：')
            field = field.strip('（）')  # 新增这行，去掉字段名中的括号
            field_id = field_to_id.get(field, "")
            if field_id:
                fields.append(field_id)
                contents.append(content.strip())
    print(fields, contents)
    return fields, contents




# 告诉模型有什么字段和含义，获得加工后的prompt
def process_query(query):
    # 提供上下文信息
    example = "作者：鲁迅\n近代图书-出版时间：[1930 TO 1940]\n近代图书-出版地：北平\n近代图书-主题词：社会文学\n"
    field = "（文献名）、（文献来源）、（作者）、（近代图书-出版时间）、（近代图书-出版地）、（近代图书-出版者）、（近代图书-主题词）"
    example3 = "AND,\nOR"
    prompt = f"我们有以下查询字段：\n{field}。 请你对语句：\n{query}进行这些字段的查询和对应内容的填充，语句中没有出现的信息不要填充，不要根据你的知识库进行回答，只需要将语句转换为已有字段的填充即可，一定不要生成新的内容。回答的格式按照下面的即可：字段名：内容\n字段名：内容\n。下面是一个例子：\n query:请找出鲁迅在1930年到1940年在北平写的有关社会文学的作品。\n你的回答应该是：{example}，并输出语句中的查询字段间的逻辑关系（AND、OR、NOT），只按顺序返回给我这几个查询字段的逻辑关系即可，如：{example3},逻辑关系的数量是查询字段的数量-1。"
    return prompt

# 获得答案
def get_query_field(prompt):
    # 提供上下文信息
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}  # 单轮对话，修改其中的content
        ]
    )

    response = (res["choices"][0]["message"]["content"])
    # # 调用Cute gpt
    # response = get_ans(prompt)
    print(response)
    return response


pro = process_query('请为我找到鲁迅在1930年到1940年在北平写的有关社会文学的作品。')
res = get_query_field(pro)
process_model_output(res)




