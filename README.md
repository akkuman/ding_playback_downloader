# 钉钉直播回放下载

## 使用

### 安装依赖

```shell
poetry install
```

或者使用

```shell
pip install -r requirements.txt
```

其中 `requirements.txt` 是使用命令 `poetry export -f requirements.txt --output requirements.txt --without-hashes` 生成的

### 修改配置

打开 `main.py`，修改其中的

```plain
# chrome.exe 的地址
__EXECUTABLE_PATH__  = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
```

为你的 chrome 路径

### 运行使用

首先打开代理

```shell
python -m mitmproxy -s ./main.py
```

默认监听本机 8080 端口

然后将钉钉流量转发到该代理

点开任意一个直播回放

然后会自动弹出浏览器要求登录钉钉，登录后即可开始自动下载
