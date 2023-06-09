# Message format
For stream messages that may be needed, I am using the same method as before [Claude-in-slack-api]() :
Content is transmitted through the `WebSocket`, every messages(on or two characters), including every step of web search will be transmitted through the Websocket
## Connect to Websocket
After `OpenAssistant()`, a WebSocket server with a random port is created
Get the connection address by `OpenAssistant().wsurl`. default is broadcast and returns the local address

## Chat message content
```json
{
    "type": "text",
    "status": status,  // True(message generation complete) or False
    "msg": msg,  // message content status:True->returns the full text or else instant character(stream)
    "user": user,   //'user' or 'Open-Assistant'
    "conversation_id": conversation_id   
}
```

## Web search content
```json
{
    "type": "web_search",
    "data": data,   // data["type"]=="web_search" is for the steps of web search or else something wrong
    "conversation_id": conversation_id   
}
```

## Example of message receive
you can see full code in [main_cmd.py](./Server/main_cmd.py)
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
	if status:  # ignore the stream character and wait for the full text
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

## Login
```python
import requests.sessions
from HuggingChat.Login import Login

email = "your email"
passwd = "password"
sign = Login(email=email, passwd=passwd, mysql=False)

# Login and save cookies
cookies: requests.sessions.RequestsCookieJar = sign.main()

# Load cookies from saved file or database
cookies: requests.sessions.RequestsCookieJar  = sign.loadCookies()
```

## Usage
### OpenAssistant(email, cookies, translater, mysql)

| params     | class                             | explanation       |
|------------|-----------------------------------|-------------------|
| email      | str                               | login email       |
| cookies    | RequestsCookieJar                 | token and hf-chat |
| translater | YDTranslate.Translater.Translater | translate api     |
| mysql      | bool                              | use mysql or not  |

#### init()
run `fetchConversations()` to get conversations, and initialize `History()`.

#### fetchConversations()
fetch every conversation and save them inside `self.conversations` with this format:  
`[{"id":conversation_id, "title": title}, ...]`

#### getData(text, web_search_id: str = "")
returns the default chat params
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
Chat.  
use `self.current_conversation` if `conversation_id` is `None` 
wait and get reply through `getReply()`   
when `web` is set to True, use `WebSearch()` search prompt on web and send in `search id`

#### getReply()
send message to open-assistant，parse response using `parseData()`

#### parseData()
parse `EventStream` and forward message through `self.WSOut.sendMessage()`

#### getTitle(conversation_id)
get summary title of the given conversation

#### createConversation(text, web: bool=False)
create a new conversation.  
save `conversation_id` and `title` in to `self.conversations` and returns the title

#### removeConversation(index: int)
delete conversation
