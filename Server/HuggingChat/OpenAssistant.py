import datetime
import logging
import uuid
import requests
import requests.utils
import requests.sessions
import json
import re

from .WebSearch import WebSearch
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
		Get conversation and initialize History()
		:return: 无
		'''
		self.fetchConversations()
		# self.setTimeSynchronizeHistory()
		self.History = History_SQL(self.email, self) if self.mysql else History(self.email, self)
	
	# def setTimeSynchronizeHistory(self):
		# self.History = History_SQL(self.email, self) if self.mysql else History(self.email, self)
		# if self.mysql:
		# 	self.History = History_SQL(self.email, self)
		# else:
		# 	self.History = History(self.email, self)
	
	def fetchConversations(self):
		'''
		Get conversation a from a html and extract them using re
		:return:
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
		GET
		:param url:
		:param params:
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
		POST
		:param url:
		:param params:
		:param data:
		:param stream:
		:return: Response
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
		random uuid
		:return: uuid hex with the format ’8-4-4-4-12‘
		'''
		uid = uuid.uuid4().hex
		return f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}"
	
	def getData(self, text, web_search_id: str = ""):
		'''
		Default data
		:param web_search_id: web_search_id
		:param text:
		:return: data
		'''
		data = {
			"inputs": text,
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
		'''
		Parser for EventStream
		:param res: requests.post(stream=True) -> Response
		:param conversation_id:
		:return: Final reply
		'''
		if res.status_code != 200:
			raise Exception(f"chat fatal: {res.status_code} - {res.text}")
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
							self.WSOut.sendMessage(status=False, msg=reply, user="Open-Assistant", conversation_id=conversation_id)
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
		Send message and Parse response
		:param web_search_id: search id
		:param conversation_id:
		:param text:
		:return: Reply text
		'''
		url = self.url_initConversation + f"/{conversation_id}"
		reply = None
		
		for i in range(3):
			data = self.getData(text, web_search_id)
			# print(data)
			res = self.requestsPost(url, stream=True, data=json.dumps(data))
			reply = self.parseData(res, conversation_id=conversation_id)
			if reply != None:
				break
		if reply == None:
			raise Exception("No reply")
		return reply
	
	def tranlate(self, text):
		'''
		Translate English -> Chinese
		:param text:  English text
		:return: Chinese text
		'''
		text = self.translater.translate(text)
		return text
	
	# def parseWebData(self, res: requests.Response, conversation_id):
	# 	if res.status_code != 200:
	# 		raise Exception("chat fatal")
	# 	index = -1
	# 	try:
	# 		for c in res.iter_content(chunk_size=1024):
	# 			chunks = c.decode("utf-8").split("\n\n")
	#
	# 			for chunk in chunks:
	# 				if chunk:
	# 					try:
	# 					# chunk = tempchunk + re.sub("^data:", "", chunk)
	# 						js = json.loads(chunk)
	# 					except:
	# 						logging.info(f"load fatal: {chunk}")
	# 						continue
	# 					try:
	# 						if js["messages"][-1]["type"] == "result":
	# 							self.WSOut.sendWebSearch(js["messages"][-1], conversation_id=conversation_id)
	# 							return js
	# 						elif len(js["messages"]) - 1 > index:
	# 							if index == -1:
	# 								self.WSOut.sendWebSearch(js["messages"][0], conversation_id=conversation_id)
	# 								index = 0
	# 							for message in js["messages"][index+1:]:
	# 								self.WSOut.sendWebSearch(message, conversation_id=conversation_id)
	# 								index += 1
	# 					except:
	# 						pass
	# 	except Exception as e:
	# 		print(e)
	# 	return
	#
	# def chatWeb(self, text: str, conversation_id=None):
	# 	'''
	# 	Start web search, parse for the final search id and implement it into chat data.
	# 	:param text:
	# 	:param conversation_id:
	# 	:return:
	# 	'''
	# 	conversation_id = self.current_conversation if not conversation_id else conversation_id
	# 	if not conversation_id:
	# 		logging.info("No conversation selected")
	# 		return None
	# 	webUrl = self.url_initConversation + f"/{conversation_id}/web-search"
	# 	js = WebSearch(webUrl + f"?prompt={text}", self.cookies.get_dict(), self.WSOut, conversation_id).getWebSearch()
	# 	web_search_id = js["messages"][-1]["id"] if js else ""
	# 	self.WSOut.sendMessage(status=True, msg=text, user="user", conversation_id=conversation_id)
	# 	self.getReply(conversation_id, text, web_search_id)
	
	def chat(self, text: str, conversation_id=None, web=False):
		'''
		Normal chat, send message and wait for reply
		:param web: use web search or not
		:param conversation_id: conversation_id
		:param text:
		:return: None since the message will be send through websocket
		'''
		conversation_id = self.current_conversation if not conversation_id else conversation_id
		if not conversation_id:
			logging.info("No conversation selected")
			return None
		web_search_id = ""
		if web:
			webUrl = self.url_initConversation + f"/{conversation_id}/web-search"
			js = WebSearch(
				webUrl + f"?prompt={text}",
				self.cookies.get_dict(),
				self.WSOut,
				conversation_id
			).getWebSearch()
			web_search_id = js["messages"][-1]["id"] if js else ""
		self.WSOut.sendMessage(status=True, msg=text, user="user", conversation_id=conversation_id)
		self.getReply(conversation_id, text, web_search_id)
	
	# eng = self.getReply(conversation, text)
	# if len(re.findall("[a-zA-Z]", eng)) > 0:
	# 	zh = self.tranlate(eng)
	# else:
	# 	zh = eng
	# return (eng, (zh))
	
	def getTitle(self, conversation_id):
		'''
		Get conversation summary
		:param conversation_id:
		:return: title
		'''
		url = self.url_initConversation + f"/{conversation_id}/summarize"
		res = self.requestsPost(url)
		if res.status_code != 200:
			raise Exception("get conversation title failed")
		js = res.json()
		return js["title"]
	
	def createConversation(self, text, web: bool=False):
		'''
		start a new conversation
		:param web: use web search or not
		:param text:
		:return: new conversation title
		'''
		data = {"model": self.model}
		res = self.requestsPost(self.url_initConversation, data=json.dumps(data))
		if res.status_code != 200:
			raise Exception("create conversation fatal")
		js = res.json()
		conversation_id = js["conversationId"]
		self.chat(text, conversation_id, web=web)
		title = self.getTitle(conversation_id)
		if not title:
			raise Exception("create conversation fatal")
		conversation = {"id": conversation_id, "title": title}
		self.conversations.append(conversation)
		# return (reply, conversation)
		self.current_conversation = conversation_id
		return title
	
	def removeConversation(self, index: int):
		'''
		Remove conversation through the index of self.conversations
		:param index:
		:return:
		'''
		if not 0 <= index <= len(self.conversations) - 1:
			logging.info("Index out of bounds\nindex超出范围")
			return
		conversation_id = self.conversations[index]["id"]
		logging.info(f"Deleting conversation <{conversation_id}>")
		url = self.url_initConversation + f"/{conversation_id}"
		res = requests.delete(url, headers=self.headers, cookies=self.cookies)
		if res.status_code != 200:
			logging.info(f"{res.text}")
			logging.info("Delete conversation fatal")
			return
		del self.conversations[index]
		if self.current_conversation == conversation_id:
			self.current_conversation = None
		return 1
	
	def getHistoriesByID(self, conversation_id=None):
		conversation_id = self.current_conversation if not conversation_id else conversation_id
		if not conversation_id:
			return []
		logging.info(f"Getting histories for {self.email}:{conversation_id}...")
		histories = self.History.getHistoriesByID(conversation_id)
		if histories == None:
			raise Exception("Something went wrong")
		else:
			
			return histories
	
	def getConversations(self):
		return self.conversations
	
	def getTextFromInput(self, addition: str = ""):
		'''
		mainly use for command line to get text using input()
		:param addition: text to be print out before the (converstation_id) >
		:return:
		'''
		while 1:
			text = input(f"{addition}({self.current_conversation}) > ")
			if not text:
				continue
			else:
				return text
	
	def switchConversation(self, option: int):
		self.current_conversation = self.conversations[option]["id"]
	
	def printOutConversations(self):
		'''
		mainly for command line usage, return conversations in a formatted text.
		:return:
		'''
		string = "* Conversations that have been established:\n* 已创建的对话: \n\n"
		for i in range(len(self.conversations)):
			string += f"	{i}. {self.conversations[i]['title']}\n"
		# string += "\n"
		return string


if __name__ == "__main__":
	# main()
	pass
