# Open-Assistant-Chinese.ver

> There's an update in hugging-chat, which requires the user to sign in (token and hf-chat cookies are required to send requests).

Using hugging-chat web API, the model that is currently available is open-assistant's model called oasst-sft-6-llama-30b

## Translator

since the model only replies in english even if it's able to process chinese, i decided to add a plugin for it, which is a translator provided by Youdao.

After reverse engineered it's web api and reconstructed it using pure python, i managed to finish this.

here's the repo: [YouDao-Translater](https://github.com/ogios/YouDao-Translater)

## Basic usage

```python
from OpenAssistant import OpenAssistant
from YDTranslate import Translater

tranlater = Translater.Translater(hot=True) # connect to the translater using default params
assistant = OpenAssistant.OpenAssistant(email, tranlater) # email is refered to the sign in email
assistant.init()

```

after `init()`, it will connect to the mysql server and synchronize the chat history down to the local database.

## mysql table structure

there's two tables named  `user` and  `conversation`

```sql
CREATETABLE `user`  (
  `email`varchar(255) CHARACTERSET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `passwd`varchar(255) CHARACTERSET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `cookies`textCHARACTERSET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  PRIMARY KEY (`username`) USING BTREE,
  UNIQUEINDEX`unique_id`(`username`ASC) USING BTREE
) ENGINE = InnoDB CHARACTERSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

CREATETABLE `conversation`  (
  `username`varchar(255) CHARACTERSET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `conversation_id`varchar(255) CHARACTERSET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `is_user`tinyint(1) NOT NULL,
  `text_eng`textCHARACTERSET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `text_zh`textCHARACTERSET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `time`datetimeNOT NULLONUPDATE CURRENT_TIMESTAMP,
  `text_id`varchar(255) CHARACTERSET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULLDEFAULTNULL
) ENGINE = InnoDB CHARACTERSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

```

## Usage

### Get chat history

by calling the function `init()` , a thread will be created to synchronize the chat histories every 15s, and then translate every single conversation and save them into the mysql server.

get histories from the database using `getHistories()`

texts won't be saved into the database in the request's process, the only way to save it is to wait for the chat history request which will happen every 15s since the uuid of every single conversation isn't within the chat responses.

```python

    def synchronizeChatHistory(self):
        '''
	download chat histories to mysql database
        :return: None
        '''
        ...

```

### Create new conversation

use function called `createConversation()` to create a new conversation

```python
    def createConversation(self, text):
        '''
	send a text before creating a new conversation
        :param string text
        :return: ((reply in eng, reply in zh_cn), (conversation id, conversation title))
        '''
        data = {"model": self.model}
        res = self.requestsPost(self.url_initConversation, data=json.dumps(data))
        # res = requests.post(self.url_initConversation, headers=self.headers, cookies=self.cookies, proxies=self.proxies)
        if res.status_code != 200:
            raiseException("create conversation fatal")
        # self.refreshCookies(res.cookies)
        js = res.json()
        conversation_id = js["conversationId"]
        reply = self.chat(conversation_id, text)
        title = self.getTitle(conversation_id)
        ifnot reply[0] andnot title:
            raiseException("create conversation fatal")
        conversation = {"id": conversation_id, "title": title}
        self.conversations.append(conversation)
        # self.saveChat(conversation_id["id"], (None, text), True, )
        return (reply, conversation)

```

the return format of `chat()` and `createConversation()`:

```python
# chat()
(reply in eng, reply in zh_cn)

# createConverstaion()
(
  (reply in eng, reply in zh_cn),
  {"id": conversation id, "title": conversation title}
)

```

### Request and Cookies

```python
    def requestsGet(self, url:str, params=None) -> requests.Response:
        '''
        GET Request
        :param url
        :param params
        :return: Response
        '''
        res = requests.get(url, params=params, headers=self.headers, cookies=self.cookies, proxies=self.proxies)
        if res.status_code == 200:
            self.refreshCookies(res.cookies)
        return res

    def requestsPost(self, url:str, params=None, data=None, stream=False) -> requests.Response:
        '''
        POST request
        :param url
        :param params
        :param data
        :param stream
        :return: Response
        '''
        res = requests.post(url, stream=stream, params=params, data=data, headers=self.headers, cookies=self.cookies, proxies=self.proxies)
        if res.status_code == 200:
            self.refreshCookies(res.cookies)
        return res
  
    def refreshCookies(self, cookies:requests.sessions.RequestsCookieJar):
        '''
	refresh every cookies that returns 
        :param cookies: Response.cookies
        :return: None
        '''
        dic = cookies.get_dict()
        for i in dic:
            self.cookies.set(i, dic[i])
        User.update({
            User.cookies: json.dumps(self.cookies.get_dict(), ensure_ascii=True)
        }).where(User.username == self.username).execute()

```

### Params

get chat params using `getData()`

set `stream=False` if want it to reply after it's done generating text.

```python
    def getData(self, text):
        '''
        params set for chat request
        :param text
        :return: dict
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

### Proxy

the default proxy is set to `http://localhost:7890`

### mysql config

set mysql user, password, database's name, host and port in this file called `mysqlconf.json`
