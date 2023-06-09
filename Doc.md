# 消息格式
为了可能被需要的流式传播，我是用的和之前 [Claude-in-slack-api]() 用的是相同的方法:  
通过 `WebSocket` 传输内容，可以说，所有消息 (包括网络搜索的，每个步骤) 每一个字符都会经过Websocket传输，就如 `EventStream` 一样

## 连接Websocket
在创建 `OpenAssistant()` 后会创建一个随机端口的 WebSocket 服务器  
通过 `OpenAssistant().wsurl` 获取连接地址，默认广播，返回本地地址

## 对话内容
传输格式如下：
```json
{
    "type": "text",
    "status": status,  // True(对话已完全生成) 或 False(仍未完全生成)
    "msg": msg,  // 消息内容 当status:True时返回完整的内容否则仅返回生成的部分字符
    "user": user,   //'user'或'Open-Assistant'
    "conversation_id": conversation_id   // 对话id
}
```

## 网络搜索步骤与内容
```json
{
    "type": "web_search",
    "data": data,   // data 中的 type 为 web_search 时即为搜索步骤，否则就是搜索失败或是模型超载
    "conversation_id": conversation_id   // 对话id
}
```

## 消息接收
这里给出简要的接收消息的方式，在 [main_cmd.py](./Server/main_cmd.py) 中更加详细
```python
from websocket import WebSocketApp
from threading import Thread
from HuggingChat.OpenAssistant import OpenAssistant
import json
import logging

def updateMSG(js):
	status = js["status"]  # status stands for whether the message complete or still generating.
	msg = js["msg"]  
	user = js["user"]  # whether this message is sent by user or Open-Assistant.
	if status:  # 由于是终端对话，所以仅看最后生成完的对话
		string = f"({user}): {msg}"
		print(string)

def updateWebSearch(js: dict):
	# print(js)
	if js["type"] == "web_search" and js.__contains__("data"):
		data: dict = js["data"]
		if data["type"] == "update" and data.__contains__("message"):
			string = f"* {data['message']}{' - '+str(data['args']) if data.__contains__('args') else ''}"
			print(string)
		elif data["type"] == "result":
			print(f"* result - {data['id']}")
		else:
			logging.error(f"Wrong step: {js}")
	else:
		logging.error(f"Wrong step: {js}")

def startWSApp(url):
	
	def on_message(wsapp, data):
		data = json.loads(data)
		type = data["type"]
		if type == "text":
			updateMSG(data)
		if type == "web_search":
			updateWebSearch(data)
		elif type == "error":
			print("error occurred: ", data["msg"])
	
	WSA = WebSocketApp(url, on_message=on_message)
	Thread(target=WSA.run_forever, daemon=True).start()

openassistant = OpenAssistant(u, cookies=cookies, tranlater=Translater(), mysql=mysql)
openassistant.init()
startWSApp(openassistant.wsurl)
```

# API

## 登录
```python
import requests.sessions
from HuggingChat.Login import Login

email = "你账号的邮箱"
passwd = "密码"
sign = Login(email=email, passwd=passwd, mysql=False)

# 登录并保存cookies
cookies: requests.sessions.RequestsCookieJar = sign.main()

# 从已保存的cookies中加载
cookies: requests.sessions.RequestsCookieJar  = sign.loadCookies()
```

## 使用
### OpenAssistant(email, cookies, translater, mysql)

| 参数         | 类型                                | 注释            |
|------------|-----------------------------------|---------------|
| email      | str                               | 登录邮箱          |
| cookies    | RequestsCookieJar                 | token与hf-chat |
| translater | YDTranslate.Translater.Translater | 翻译接口          |
| mysql      | bool                              | 是否接入mysql     |

#### init()
运行 `OpenAssistant().fetchConversations()` 获取所有对话并初始化 `History()`.

#### fetchConversations()
获取所有对话，并以 `[{"id":conversation_id, "title": title}, ...]` 的形式存入 `self.conversations`

#### getData(text, web_search_id: str = "")
返回默认对话参数，我就不在这里解释每个参数的的意义了：
```json
{
    "inputs": text,
    "parameters": {
        "temperature": 0.9,
        "top_p": 0.95,
        "repetition_penalty": 1.2,
        "top_k": 50,
        "truncate": 1024,
        "watermark": false,
        "max_new_tokens": 1024,
        "stop": [
            "</s>"
        ],
        "return_full_text": false
    },
    "options": {
        "id": self.getUUID(),
        "response_id": self.getUUID(),
        "is_retry": false,
        "use_cache": false,
        "web_search_id": web_search_id
    },
    "stream": true,
}
```
#### chat(text: str, conversation_id=None, web=False)
对话，当`conversation_id`为`None`时默认使用 `self.current_conversation`  
通过 `getReply()` 等待并获取接收的消息   
当web为True，调用 `WebSearch()` 进行网络搜索并传入 `search id`

#### getReply()
发送消息，并通过 `parseData()` 解析

#### parseData()
解析 `EventStream` 发送的内容并通过 `self.WSOut.sendMessage()` 发送

#### getTitle(conversation_id)
获取当前对话的总结标题

#### createConversation(text, web: bool=False)
创建新对话，获取总结标题后添加至 `self.conversations` 中  
返回总结标题

#### removeConversation(index: int)
删除对话

