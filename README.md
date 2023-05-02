# Open-Assistant-Chinese.ver

这个Open-Assistant模型现阶段几乎没有任何作用，不过可以本地部署与实现。

## 说明
我这里抓包的是huggingface的网页接口，模型是OpenAssistant/oasst-sft-6-llama-30b  
速度不慢，不过基本都是挂着梯子用的，可以为其打造一个api放服务器上

## 有道翻译接口
使用的是我自己逆向之后的纯python实现的接口，不需要js  
传送门: [YouDao-Translater](https://github.com/ogios/YouDao-Translater)

## Open-Assistant创建
使用下面的代码创建与初始化接口，连接mysql并同步对话内容：
```python
from OpenAssistant import OpenAssistant
from YDTranslate import Translater

tranlater = Translater.Translater(hot=True) #使用默认参数的有道翻译，不重新请求key
assistant = OpenAssistant.OpenAssistant(username, tranlater) #username为mysql数据库中用户的名字
assistant.init()
```
这样就会自动创建并连接mysql，同步cookies与对话内容

## mysql数据库表结构
共两张表，`user` 与 `conversation`
```sql
CREATE TABLE `user`  (
  `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `passwd` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `cookies` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  PRIMARY KEY (`username`) USING BTREE,
  UNIQUE INDEX `unique_id`(`username` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

CREATE TABLE `conversation`  (
  `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `conversation_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `is_user` tinyint(1) NOT NULL,
  `text_eng` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `text_zh` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `time` datetime NOT NULL ON UPDATE CURRENT_TIMESTAMP,
  `text_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;
```

## 使用
> 仅给出部分方法的使用

### 提取旧的对话内容
在调用 `init()` 初始化后会创建一个线程，每30秒同步一次对话内容
使用getHistories()获取旧的记录
```python
class OpenAssistant:
    ...
  def getHistories(self, conversation_id=None) -> List[Conversation]:
    '''
    从在数据库中已保存的conversation中按用户名提取所有对话
    :return: List[User记录]
    '''
    if conversation_id != None:
      return Conversation.select().where(
        Conversation.username == self.username and Conversation.conversation_id == conversation_id
      ).execute()
    return Conversation.select().where(Conversation.username == self.username).execute()
    
    ...
    
chat_history = openassistant.getHistories(conversation_id=conversation_id)
for c in chat_history:
  text: str = c.text_eng if not c.text_zh else c.text_zh
  text.replace("\n","\\n")
  hist = f"({'user' if c.is_user else 'assist'}): {text}"
  print(hist)
```

### 创建新对话
使用 `createConversation()` 创建新的对话
```python
class OpenAssistant:
...
  def createConversation(self, text):
    '''
    创建新对话, 需要先进行一次对话获取标题
    :param text: 对话
    :return: (英文文本, 中文文本)
    '''
    res = self.requestsPost(self.url_initConversation)
    # res = requests.post(self.url_initConversation, headers=self.headers, cookies=self.cookies, proxies=self.proxies)
    if res.status_code != 200:
      raise Exception("create conversation fatal")
    # self.refreshCookies(res.cookies)
    js = res.json()
    conversation_id = js["conversationId"]
    reply = self.chat(conversation_id, text)
    title = self.getTitle(conversation_id)
    if not reply[0] and not title:
      raise Exception("create conversation fatal")
    conversation = {"id": conversation_id, "title": title}
    self.conversations.append(conversation)
    return (reply, conversation)
...

openassistant.init()
conversation = None
if len(openassistant.conversations) > 0:
  conversation_detail = openassistant.conversations[0]
else:
  conversation = openassistant.createConversation("every respond i need you to add two symbols '\n', can you do it?")
  print(f"reply: {conversation[0]}", f"conversation_detail: {conversation[1]}", sep="\n")
  conversation_detail = conversation[1]
conversation_id = conversation_detail["id"]
print(f"Title: {conversation_detail['title']}")
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
	def requestsGet(self, url:str, params=None) -> requests.Response:
		'''
		GET请求接口
		:param url: url(必填)
		:param params: params(非必须)
		:return: Response
		'''
		res = requests.get(url, params=params, headers=self.headers, cookies=self.cookies, proxies=self.proxies)
		if res.status_code == 200:
			self.refreshCookies(res.cookies)
		return res
	
	def requestsPost(self, url:str, params=None, data=None, stream=False) -> requests.Response:
		'''
		POST请求接口
		:param url: url(必填)
		:param params:
		:param data:
		:param stream: 流传输(默认不使用)
		:return:
		'''
		res = requests.post(url, stream=stream, params=params, data=data, headers=self.headers, cookies=self.cookies, proxies=self.proxies)
		if res.status_code == 200:
			self.refreshCookies(res.cookies)
		return res
    
	def refreshCookies(self, cookies:requests.sessions.RequestsCookieJar):
		'''
		用于请求完后刷新和维持cookie
		:param cookies: 请求后的cookie，从 Response.cookies 中提取
		:return: 无
		'''
		dic = cookies.get_dict()
		for i in dic:
			self.cookies.set(i, dic[i])
		User.update({
			User.cookies: json.dumps(self.cookies.get_dict(), ensure_ascii=True)
		}).where(User.username == self.username).execute()
```

### 对话参数
对话参数使用getData()获取与设置
```python
	def getData(self, text):
		'''
		对话请求的data模板
		:param text: 对话内容
		:return: data本身
		'''
		data = {
			"inputs": text.encode("utf-8").decode("latin1"),
			"parameters": {
				"temperature": 0.9,
				"top_p": 0.95,
				"repetition_penalty": 1.2,
				"top_k": 50,
				"truncate": 1024,
				"watermark": False,
				"max_new_tokens": 1024,
				"stop": [
					"</s>"
				],
				"return_full_text": False
			},
			"options": {
				"id": self.getUUID(),
				"is_retry": False,
				"use_cache": False
			},
			"stream": True,
		}
		return data
```
这里的参数都是huggingface里无法直接设置的，但是在这里可以手动调整参数，或者去open-assistant官网尝试更多的模型与参数

### 代理
默认是有代理的，clash的7890端口

### mysql配置
在文件 `mysqlconf.json` 里设置用户，密码，数据库名，主机地址，端口这些信息
