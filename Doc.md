
```python
from HuggingChat.OpenAssistant import OpenAssistant
from HuggingChat.Login import Login
from YDTranslate.Translater import Translater

def startWSApp(url):
	global WSA
	
	def on_open(wsapp):
		global WSA_OPEN
		WSA_OPEN = True
	def on_message(wsapp, data):
		data = json.loads(data)
		type = data["type"]
		if type == "text":
			updateMSG(data)
		if type == "web_search":
			updateWebSearch(data)
		elif type == "error":
			print("error occurred: ", data["msg"])
	
	WSA = WebSocketApp(url, on_message=on_message, on_open=on_open)
	Thread(target=WSA.run_forever, daemon=True).start()

tranlater = Translater.Translater(hot=True) #使用默认参数的有道翻译，不重新请求key
assistant = OpenAssistant.OpenAssistant(email, Translater()) #email为huggingchat的登录邮箱
assistant.init()
```

## 使用

> 仅给出部分方法的使用

### 提取旧的对话内容

在调用 `init()` 初始化后会创建一个线程 `synchronizeChatHistory()` ，每15秒同步一次对话内容并保存至mysql数据库中
使用getHistories()从mysql中获取旧的记录

需要注意的是，直接发送对话后并不会将对话内容保存至数据库中，需要等待同步历史记录，这是因为直接对话时服务器并不会返回这句话的uuid，同步历史记录时才会给出

```python
	def synchronizeChatHistory(self):
		'''
		根据huggingface服务器保存的对话记录保存至数据库中
		:return: 无
		'''
		...
```

### 创建新对话

使用 `createConversation()` 创建新的对话

```python
```

正常的chat()与createConversation()返回的内容格式分别如下:

```python
# chat()
(英文回复, 中文回复)

# createConverstaion()
(
  (英文回复, 中文回复),
  {"id": 对话id, "title": 对话的标题}
)
```

### 持久化

对于GET与POST请求分别套了两个方法，并配合refreshCookies()进行cookies的持久化

```python

```

### 对话参数

对话参数使用getData()获取与设置

```python

```

这里的参数都是huggingface里无法直接设置的，但是在这里可以手动调整参数，或者去open-assistant官网尝试更多的模型与参数
