# STsearch_enhancement
STsearch_enhancement1_0.py文件中有openai的key还有代理端口，需要vpn能力
举例：
在STsearch_enhancement1_0.py中
os.environ["http_proxy"] = "http:192.168.1.100:1234"     # 修改为自己的代理端口
os.environ["https_proxy"] = "https:192.168.1.100:1234"    # 修改为自己的代理端口
那么在STapp.py文件中，对应的
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # 您可以根据需要更改端口号
    # host='127.0.0.1'则改为只在主机上使用
那么在STtest.py文件中：
url = "http://192.168.1.100:5000/get_result"

  


