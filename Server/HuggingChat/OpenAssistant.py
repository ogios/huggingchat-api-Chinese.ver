import datetime
import logging
import time
import traceback
import uuid

# import pycurl
import requests
import requests.utils
import requests.sessions
import json
import re
from threading import Thread

# import urllib.parse
# from six import StringIO

from .History import History_SQL, History
from .WSServer import WSOut
from YDTranslate import Translater


def dictToString(cookies: dict):
	cookie = ""
	for i in cookies:
		cookie += f"{i}={cookies[i]}; "
	return cookie


class OpenAssistant:
	def __init__(
			self,
			email: str,
			cookies: requests.sessions.RequestsCookieJar,
			tranlater: Translater.Translater = None,
			mysql: bool = False
	):
		
		self.email = email
		self.model = "OpenAssistant/oasst-sft-6-llama-30b-xor"
		self.url_index = "https://huggingface.co/chat/"
		self.url_initConversation = "https://huggingface.co/chat/conversation"
		self.headers = {
			"Referer": "https://huggingface.co/chat",
			"Content-Type": "application/json",
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.64",
		}
		# self.proxies = {
		# 	"http": "http://127.0.0.1:7890",
		# 	"https": "http://127.0.0.1:7890"
		# }
		self.translater = tranlater
		self.cookies = cookies
		self.conversations = list()
		self.mysql = mysql
		self.current_conversation = None
		self.WSOut = WSOut()
		self.wsurl = self.WSOut.getUrl()
		self.History = None
	
	def init(self):
		'''
		Open-Assistant接口初始化总方法：
		1. 数据库中提取已保存cookies
		2. 提取已有对话
		3. 同步对话
		:return: 无
		'''
		self.fetchConversations()
		self.setTimeSynchronizeHistory()
	
	def setTimeSynchronizeHistory(self):
		def loop():
			try:
				while 1:
					time.sleep(15)
					# print("正在同步信息...")
					self.History.synchronizeChatHistory()
			except:
				print("同步消息失效!")
				traceback.print_exc()
		
		if self.mysql:
			self.History = History_SQL(self.email, self)
			self.History.synchronizeChatHistory()
			Thread(target=loop, daemon=True).start()
		else:
			self.History = History(self.email, self)
	
	def fetchConversations(self):
		'''
		从 html 中提取 huggingface 服务器上已有的所有对话id
		:return: 无，将conversation以 id 与 title 的键值对形式存储
		'''
		res = self.requestsGet(self.url_index)
		html = res.text
		conversation_ids = list(set(re.findall('href="/chat/conversation/(.*?)"', html)))
		for i in conversation_ids:
			title = re.findall(f'href="/chat/conversation/{i}.*?<div class="flex-1 truncate">(.*?)</div>', html, re.S)
			if len(title) > 0:
				title = title[0].strip()
			else:
				title = "未获取到title"
			self.conversations.append({"id": i, "title": title})
	
	def requestsGet(self, url: str, params=None, stream=False) -> requests.Response:
		'''
		GET请求接口
		:param url: url(必填)
		:param params: params(非必须)
		:return: Response
		'''
		res = requests.get(
			url,
			params=params,
			headers=self.headers,
			cookies=self.cookies,
			stream=stream,
			# proxies=self.proxies
		)
		# if (res.status_code == 200) & (self.mysql):
		# 	self.refreshCookies(res.cookies)
		return res
	
	def requestsPost(self, url: str, headers=None, params=None, data=None, stream=False) -> requests.Response:
		'''
		POST请求接口
		:param url: url(必填)
		:param params:
		:param data:
		:param stream: 流传输(默认不使用)
		:return:
		'''
		res = requests.post(
			url,
			stream=stream,
			params=params,
			data=data,
			headers=self.headers if not headers else headers,
			cookies=self.cookies,
			# proxies=self.proxies,
		)
		# if (res.status_code == 200) & (self.mysql):
		# 	self.refreshCookies(res.cookies)
		return res
	
	def getUUID(self):
		'''
		随机生成对话标识id
		:return: uuid的十六进制配上8-4-4-4-12的分隔
		'''
		uid = uuid.uuid4().hex
		return f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}"
	
	def getData(self, text, web_search_id: str = ""):
		'''
		对话请求的data模板
		:param web_search_id: web_search_id
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
				"response_id": self.getUUID(),
				"is_retry": False,
				"use_cache": False,
				"web_search_id": web_search_id
			},
			"stream": True,
		}
		return data
	
	def getTime(self):
		return str(datetime.datetime.now())
	
	def parseData(self, res: requests.Response, conversation_id):
		if res.status_code != 200:
			raise Exception("chat fatal")
		reply = None
		for c in res.iter_content(chunk_size=1024):
			chunks = c.decode("utf-8").split("\n\n")
			tempchunk = ""
			for chunk in chunks:
				if chunk:
					chunk = tempchunk + re.sub("^data:", "", chunk)
					try:
						js = json.loads(chunk)
						tempchunk = ""
					except:
						tempchunk = chunk
						continue
					try:
						if (js["token"]["special"] == True) & (js["generated_text"] != None):
							reply = js["generated_text"]
							reply = self.tranlate(reply)
							self.WSOut.sendMessage(status=True, msg=reply, user="Open-Assistant", conversation_id=conversation_id)
						else:
							reply = js["token"]["text"]
							self.WSOut.sendMessage(status=False, msg=reply, user="Open-Assistant", conversation_id=conversation_id)
					except:
						print(js)
		return reply
	
	def getReply(self, conversation_id, text, web_search_id: str = ""):
		'''
		对话入口
		:param conversation_id: conversation_id
		:param text: 语句
		:return: 回复(使用流获取但并不以流形式返回)
		'''
		url = self.url_initConversation + f"/{conversation_id}"
		reply = None
		
		for i in range(3):
			data = self.getData(text, web_search_id)
			res = self.requestsPost(url, stream=True, data=json.dumps(data, ensure_ascii=False))
			reply = self.parseData(res, conversation_id=conversation_id)
			if reply != None:
				break
		if reply == None:
			raise Exception("No reply")
		return reply
	
	def tranlate(self, text):
		'''
		将回复的英文翻译为英文，接口为有道
		:param text:  英文文本
		:return: 中文文本
		'''
		text = self.translater.translate(text)
		return text
	
	def parseWebData(self, res: requests.Response, conversation_id):
		if res.status_code != 200:
			raise Exception("chat fatal")
		index = -1
		try:
			for c in res.iter_content(chunk_size=1024):
				chunks = c.decode("utf-8").split("\n\n")
				
				for chunk in chunks:
					if chunk:
						try:
						# chunk = tempchunk + re.sub("^data:", "", chunk)
							js = json.loads(chunk)
						except:
							logging.debug(f"load fatal: {chunk}")
						try:
							if js["messages"][-1]["type"] == "result":
								self.WSOut.sendWebSearch(js["messages"][-1], conversation_id=conversation_id)
								return js
							elif len(js["messages"]) - 1 > index:
								if index == -1:
									self.WSOut.sendWebSearch(js["messages"][0], conversation_id=conversation_id)
									index = 0
								for message in js["messages"][index+1:]:
									self.WSOut.sendWebSearch(message, conversation_id=conversation_id)
									index += 1
						except:
							pass
		except Exception as e:
			print(e)
			
		return
	
	# def __pyget(self, url):
	# 	sio = StringIO()
	#
	# 	c = pycurl.Curl()
	# 	c.setopt(pycurl.URL, url)
	# 	c.setopt(pycurl.REFERER, url)
	# 	c.setopt(pycurl.HTTPHEADER, ['Connection: close', 'Cache-Control: max-age=0',
	# 	                             'Accept: */*',
	# 	                             'User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36',
	# 	                             'Accept-Language: zh-CN,zh;q=0.8'])
	# 	c.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_0)
	# 	c.setopt(pycurl.COOKIE, dictToString(self.cookies.get_dict()))
	# 	c.setopt(pycurl.HTTPGET, 1)
	# 	# c.setopt(pycurl.POSTFIELDS, urllib.parse.urlencode(data, True))
	# 	c.setopt(pycurl.CONNECTTIMEOUT, 300)
	# 	c.setopt(pycurl.TIMEOUT, 300)
	# 	c.setopt(pycurl.WRITEFUNCTION, sio.write)
	#
	# 	try:
	# 		c.perform()
	# 	except Exception as ex:
	# 		# print 'error', ex
	# 		pass
	#
	# 	c.close()
	#
	# 	resp = sio.getvalue()
	# 	sio.close()
		
		# return resp
	
	def chatWeb(self, text: str, conversation_id=None) -> dict:
		conversation_id = self.current_conversation if not conversation_id else conversation_id
		if not conversation_id:
			logging.debug("No conversation selected")
			return None
		# webUrl = self.url_initConversation + f"/{conversation_id}/web-search?prompt={text}"
		webUrl = self.url_initConversation + f"/{conversation_id}/web-search"
		params = {
			"prompt": text
		}
		res = self.requestsGet(webUrl, params, stream=True)
		js = self.parseWebData(res, conversation_id)
		# res = self.__pyget(webUrl)
		# print(res)
		# js = json.loads(res)
		# print(res)
		# print(js)
		web_search_id = js["messages"][-1]["id"] if js else ""
		# if js:
		# 	web_search_id = js["messages"][-1]["id"]
		self.getReply(conversation_id, text, web_search_id)
	
	def chat(self, text: str, conversation_id=None):
		'''
		外都对话接口
		:param conversation_id: conversation_id
		:param text: 文本
		:return: (英文文本, 中文文本)
		'''
		conversation_id = self.current_conversation if not conversation_id else conversation_id
		if not conversation_id:
			logging.debug("No conversation selected")
			return None
		self.WSOut.sendMessage(status=True, msg=text, user="user", conversation_id=conversation_id)
		self.getReply(conversation_id, text)
	
	# eng = self.getReply(conversation, text)
	# if len(re.findall("[a-zA-Z]", eng)) > 0:
	# 	zh = self.tranlate(eng)
	# else:
	# 	zh = eng
	# return (eng, (zh))
	
	def getTitle(self, conversation_id):
		'''
		获取该对话的标题
		:param conversation_id:
		:return: 标题文本
		'''
		url = self.url_initConversation + f"/{conversation_id}/summarize"
		res = self.requestsPost(url)
		if res.status_code != 200:
			raise Exception("get conversation title failed")
		js = res.json()
		return js["title"]
	
	def createConversation(self, text, web: bool=False):
		'''
		创建新对话, 需要先进行一次对话获取标题
		:param text: 对话
		:return: ((英文文本, 中文文本), (对话id, 对话标题))
		'''
		data = {"model": self.model}
		res = self.requestsPost(self.url_initConversation, data=json.dumps(data))
		if res.status_code != 200:
			raise Exception("create conversation fatal")
		js = res.json()
		conversation_id = js["conversationId"]
		if web:
			self.chatWeb(text, conversation_id)
		else:
			self.chat(text, conversation_id)
		title = self.getTitle(conversation_id)
		if not title:
			raise Exception("create conversation fatal")
		conversation = {"id": conversation_id, "title": title}
		self.conversations.append(conversation)
		# return (reply, conversation)
		self.current_conversation = conversation_id
		return title
	
	def getHistoriesByID(self, conversation_id=None):
		conversation_id = self.current_conversation if not conversation_id else conversation_id
		if not conversation_id:
			return []
		logging.debug(f"Getting histories for {self.email}:{conversation_id}...")
		histories = self.History.getHistoriesByID(conversation_id)
		if histories == None:
			raise Exception("Something went wrong")
		else:
			
			return histories
	
	def getConversations(self):
		return self.conversations
	
	def getTextFromInput(self):
		while 1:
			text = input(f"({self.current_conversation}) > ")
			if not text:
				continue
			else:
				return text
	
	def switchConversation(self, option: int):
		self.current_conversation = self.conversations[option]["id"]
	
	def printOutConversations(self):
		string = "* Conversations that have been established: \n\n"
		for i in range(len(self.conversations)):
			string += f"	{i}. {self.conversations[i]['title']}\n"
		string += "\n"
		return string


if __name__ == "__main__":
	# main()
	pass
