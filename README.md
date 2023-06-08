# Huggingchat-Chinese.ver

中文 | [English](README_en.md)

> 暂时仅提供命令行终端聊天版本，fastapi后端版本还未完成，不过接口都是一样的

[//]: # ()
[//]: # (> 2023.6.4-22:46: 今天为之后的大更新铺垫了很多，重新构建了整个框架，但是调整说明明天再说，这会太晚了)

[//]: # ()
[//]: # (> 2023.6.6-00:30: 依旧，加的东西蛮多的，明个有时间再讲，还遇到了棘手的问题，不过暂时找到了缓解的方法)

稍微小提一嘴，huggingface的登录竟然是明文诶，没任何加密

如果可以用的话给个⭐呗🥺

## 说明

抓包的是huggingface的网页接口  
模型是 `OpenAssistant/oasst-sft-6-llama-30b`

由于时间关系，现在只做了命令行版本，fastapi配合网页的版本的暂时没时间写，搁置了  
不过用的接口都是相同的，感兴趣的话可以配合这个自己做。

下面的视频介绍了如何使用: https://www.bilibili.com/video/BV12h4y1G7Zc

## 有道翻译接口

由于使用的语言模型不会返回中文，即便模型有一定能力可以处理中文输入。所以为其加上了翻译来方便阅读

使用的是我自己逆向之后的纯python实现的接口，不需要js
传送门: [YouDao-Translater](https://github.com/ogios/YouDao-Translater)

<details>


<summary>

## 登录到huggingface

</summary>

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


</details>


<details>

<summary>

## 基本使用方法

</summary>

### 创建连接
```shell
python main_cmd.py -u <邮箱> -p
```
| 参数      |                 |
|---------|-----------------|
| -u      | 账号的邮箱(可选)       |
| -p      | 是否输入密码(可选)      |
| --mysql | 是否连接mysql(可选)   |
| -f      | 忽略已保存信息强制登录(可选) |

连接mysql前需要在 `mysqlconf.json` 文件中修改配置并提前创建名为 `open-assistant` 的数据库
或是修改 `database` 你用的别的数据库名
```json
{
  "sqluser": "",
  "sqlpass": "",
  "database": "open-assistant",
  "host": "127.0.0.1",
  "port": 3306
}
```

### 命令行
处于命令行模型时输入 `/`+`命令` 执行命令，除此之外都算作发送对话的文本

| 命令         |                   |
|------------|-------------------|
| exit       | 退出程序              |
| ls         | 查看所有对话            |
| cd <index> | 进入某个对话            |
| web        | 切换对话状态(普通/接入网络搜索) |
| old        | 查看历史记录            |
| new        | 进入新建对话状态          |
| rm <index> | 删除对话              |
| eng        | 输出上一句回复的原文(英文)    |

示例:
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

在输入 `/new` 后进入新建对话模式，仅支持 `/web` 开关网络搜索和 `/exit` 退出新建对话模式: 

新建对话示例:
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

## 其他

</summary>


### 关于网络搜索功能
#### 使用情况
我从前三四天发现聊天窗口多了一个开关网络搜索的按钮之后就打算把整个框架重构一下，然后加上网络搜索接口  
但是，今天是6月7号，这才几天，已经被用的经常出现超载了，一开始其实比现在是快蛮多的，虽然还是会等一小段时间。  
但是现在，经常超载，好不容易能用还老卡。

#### 制作过程
我并没有详细对http请求进行过一个详细的学习和了解，只会用一些平常的，这导致了下面极其的耗费时间。

这次的网络搜索接口实在把我整的有些不会了，一开始使用的是 `requests.get(stream=True)` 但经常会报错chunk的问题，我仔细看了一下发现他和对话的消息流还有点不一样。  
对话使用的是 `EventStream`，但这个并不是，而是搜索模块每经历一个步骤返回一次，期间依旧保持连接。因为报错的原因我还在网上搜来搜去，搜到都是些什么http1.0而非http1.1的内容，requests在处理这块的问题有些bug之类的。  
不过最后还是解决了。(大概吧, 至少暂时还没报错) 

### 关于英译中
每次对话返回的内容会被翻译为中文。

对于历史信息来说，没开启mysql的话会实时获取历史记录，但不会翻译。  
而如果开启了mysql，则会每过15秒同步并翻译历史记录到数据库，需要时直接从数据库中提取翻译后的内容。


</details>


<details>

<summary>

## 报错

</summary>

### Ubuntu安装pycurl报错
```shell
apt-get install libcurl4-gnutls-dev, libgnutls28-dev
```
如果可以的话尽量更新一下 `python3-dev` 和 `libpython3-dev` 等  

CentOS等系统报错网上搜一下吧，我没试过www

</details>

