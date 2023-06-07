# Huggingchat-Chinese.ver

> For now, i can only provide terminal version. fastapi and web's version are not done yet since i'm quite busy these days.  
> but the interfaces are the same.

[//]: # ()
[//]: # (> 2023.6.4-22:46: 今天为之后的大更新铺垫了很多，重新构建了整个框架，但是调整说明明天再说，这会太晚了)

[//]: # ()
[//]: # (> 2023.6.6-00:30: 依旧，加的东西蛮多的，明个有时间再讲，还遇到了棘手的问题，不过暂时找到了缓解的方法)

Leave a ⭐ if you like it🥺

## Instructions

Hugging-chat's web api. The current model is `OpenAssistant/oasst-sft-6-llama-30b`.


## Translator

since the model only replies in english even if it's able to process chinese, i decided to add a plugin for it, which is a translator provided by Youdao.

After reverse engineered its web api and reconstructed it using pure python, i managed to finish this.

here's the repo: [YouDao-Translater](https://github.com/ogios/YouDao-Translater)

<details>


<summary>

## Log in into Hugging-face

</summary>

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


</details>


<details>

<summary>

## Basic usage

</summary>

### Create Connection
```shell
python main_cmd.py -u <email> -p
```
| Args    |                                              |
|---------|----------------------------------------------|
| -u      | Email(optional)                              |
| -p      | Whether to input password(option)            |
| --mysql | Whether to connect to mysql(optional)        |
| -f      | Ignore the saved cookies and login(optional) |

You need to do some configuration in a file named `mysqlconf.json` before connecting to MySQL  
And also, create a database named `open-assistant` or change the database in the configuration file to the one you use.  
```json
{
  "sqluser": "",
  "sqlpass": "",
  "database": "open-assistant",
  "host": "127.0.0.1",
  "port": 3306
}
```

### Commands
Format: `/`+`command`

| Command    |                                 |
|------------|---------------------------------|
| exit       | exit the program                |
| ls         | list all conversations          |
| cd <index> | cd into the chosen conversation |
| web        | activate `Search web` or not    |
| old        | check conversation history      |
| new        | get into new conversation       |
| rm <index> | remove the chosen conversation  |

Example:
```
(None) > /ls
#* Conversations that have been established:
#
#        0. Assistant: "It's February 24th."
#        1. Today is Wednesday, July 12th, 2034
#        2. "What is today's date?"
#        3. "April 2nd."
#

(None) > /cd 0
(647e09ccabd9de3d82d6fba0) > hi
#(user): hi
#(Open-Assistant): ...
(647e09ccabd9de3d82d6fba0) > /web
#WEB_SEARCH is set to `True`
(647e09ccabd9de3d82d6fba0) > hi
#{'type': 'web_search', 'data': {'type': 'update', 'message': 'Injecting summary', 'args': ['"This is a search result page from iStock, a website that offers stock photography, illu
#strations, and videos. It appears to be related to Memorial Day trending searches, but it\'s not clear how or why that relates to German shepherd puppies. There are some links unde
#r the header \\"Explore\\" which offer curated collections such as signature collection and essentials collection; however these do not seem to have any specific relation with germ
#an shepherd puppies either.\\nThe queries mentioned on this page include Fireworks, Pride Data Timelapse Beach, Aerial views of nature etc . This suggest the user searched at wrong
# timeframe, there might have been other pages available at different point of time containing more accurate results."']}, 'conversation_id': '647f33d14f9cfed1cb9c9b01'}
#{'type': 'web_search', 'data': {'type': 'result', 'id': '647f33e74f9cfed1cb9c9b03'}, 'conversation_id': '647f33d14f9cfed1cb9c9b01'}
#(user): hi
#
#(Open-Assistant): 你好!今天我能为您做些什么?你需要我帮你找到某个主题的信息吗?或者你有问题要问我吗?如果有什么需要我帮忙的，请尽管开口。
```

Type `/new` to get into a new conversation, it only supports `/exit` to close the new conversation before you start it or `/web` to activate or deactivate `Search web`

Example of creating a new conversation:
```
(None) > /new
#Input the first message you want to send (use `/exit` to get back): 
#输入创建对话的第一个消息 (使用`/exit`退出新建对话): 
(new) (None) > hi
(user): hi
(Open-Assistant): ...
(647e09ccabd9de3d82d6fba0) > 
```


</details>


<details>

<summary>

## Nothing

</summary>


### Things about "Search web"
#### Lag

Days before, I noticed that the chat window has added a button to enable web search. Then I decided to reconstruct the code and add a web search interface.  
But only a few days passed, however, it gets overloaded due to high demands. It was pretty fast the day I found it.  
If you're actually using this, be ready since it may cost a lot of time and even fail to work due to model overloads.  
#### Something about this api's request

Before this, I was just simply using `requests.get(stream=True)` to send requests, but it doesn't work this time.  
`Search web`'s api is not like chat which is just a `EventStream`.  
It sometimes raises an exception about chunks, I haven't dug deeper into it, what I found online was just something about `http1.0` and `http1.1`, and problems about `requests` have trouble handling it.  
But finally i managed to get away with it. (At least there isn't a single error occurred besides from model overloads)  

### english -> chinese

Every single response will be translated into Chinese.

But for histories, it will get histories instantly but without translation if it's not connected to mysql.  
On the other hand, if you do, then it will synchronize and translate histories every 15s and save them into the database.

</details>

