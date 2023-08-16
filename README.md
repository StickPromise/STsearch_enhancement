# STsearch_enhancement
STsearch_enhancement 
是一个用于增强检索的 Python 项目。本文档提供了如何部署和运行项目的说明。

## 系统要求

- Python 3.10 或更高版本

## 安装步骤
### 1. 克隆或下载项目

首先，将项目克隆或下载到本地计算机。

### 2. 创建虚拟环境

在项目根目录下，创建一个新的虚拟环境：

python3 -m venv myenv

激活虚拟环境：
在 Windows 上：

myenv\Scripts\activate

安装依赖项
使用 requirements.txt 文件安装项目所需的依赖项：

pip install -r requirements.txt

运行项目
在虚拟环境中，运行项目的主要 Python 文件：

python STsearch_enhancement3_0.py


####注释####
STsearch_enhancement1_0.py文件中有openai的key还有代理端口，需要vpn能力
举例：
在STsearch_enhancement1_0.py中
os.environ["http_proxy"] = "http:192.168.1.100:1234"     # 修改为自己的代理端口
os.environ["https_proxy"] = "https:192.168.1.100:1234"    # 修改为自己的代理端口
那么在STapp.py文件中，对应的
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)  # 您可以根据需要更改端口号
    # host='127.0.0.1'则改为只在主机上使用
那么在STtest.py文件中：
url = "http://192.168.1.100:5001/get_result"

  


