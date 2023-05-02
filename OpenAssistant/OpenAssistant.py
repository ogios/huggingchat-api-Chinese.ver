import datetime
import time
import traceback
import uuid
from threading import Thread
from typing import List

import requests
import requests.utils
import requests.sessions
import json
import re
from YDTranslate import Translater
from OpenAssistant.SQL import User, Conversation



class OpenAssistant:
	def __init__(self, username, tranlater:Translater.Translater):
		'''
		:param username: 用户昵称(非open-assistant，而是数据库中表里存的)
		:param tranlater: 翻译接口
		'''
		self.username = username
		self.url_index = "https://huggingface.co/chat/"
		self.url_initConversation = "https://huggingface.co/chat/conversation"
		self.headers = {
			"Referer": "https://huggingface.co/",
			"Content-Type": "application/json",
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.64",
		}
		self.proxies = {
			"http": "http://127.0.0.1:7890",
			"https": "http://127.0.0.1:7890"
		}
		self.tranlater = tranlater
		self.cookies = requests.sessions.RequestsCookieJar()
		self.conversations = list()
		
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
	
	def getUUID(self):
		'''
		随机生成对话标识id
		:return: uuid的十六进制配上8-4-4-4-12的分隔
		'''
		uid = uuid.uuid4().hex
		return f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}"
	
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
	
	def getConversations(self, html):
		'''
		从 html 中提取 huggingface 服务器上已有的所有对话id
		:param html: huggingface请求主页，conversation并没有正式接口，只能通过html提取
		:return: 无，将conversation以 id 与 title 的键值对形式存储
		'''
		conversation_ids = list(set(re.findall('href="/chat/conversation/(.*?)"', html)))
		for i in conversation_ids:
			title = re.findall(f'href="/chat/conversation/{i}.*?<div class="flex-1 truncate">(.*?)</div>', html)
			if len(title) > 0:
				title = title[0]
			else:
				title = "未获取到title"
			self.conversations.append({"id": i, "title": title})
			
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
		
	def getHistoyTextId(self):
		'''
		从所有conversation中提取每句话的对话id
		:return: List[对话id]
		'''
		# histories:List[Conversation] = self.getHistories()
		histories = Conversation.select(Conversation.text_id).where(Conversation.username == self.username).execute()
		return [c.text_id for c in histories]

	def getTime(self):
		return str(datetime.datetime.now())
	
	def synchronizeChatHistory(self):
		'''
		根据huggingface服务器保存的对话记录保存至数据库中
		:return: 无
		'''
		
		# 单个用户所有记录
		histories = []
		existed_texts = self.getHistoyTextId()
		for i in self.conversations:
			url = self.url_initConversation + f"/{i['id']}/__data.json?x-sveltekit-invalidated=_1"
			res = self.requestsGet(url)
			# res = requests.get(url, headers=self.headers, cookies=self.cookies, proxies=self.proxies)
			if res.status_code != 200:
				print("synchronize chat history fatal")
			# self.refreshCookies(res.cookies)
			data = res.json()["nodes"]
			history = None
			for dic in data:
				if dic.__contains__("data"):
					history = dic["data"]
			if history:
				for his in history:
					if isinstance(his, dict):
						if his.__contains__("content"):
							if history[his["id"]] in existed_texts:
								continue
							histories.append({
								"username": self.username,
								"conversation_id": i["id"],
								"is_user": 1 if history[his["from"]] == "user" else 0,
								"text_eng": history[his["content"]],
								"text_zh": "",
								"time": self.getTime(),
								"text_id": history[his["id"]],
							})
		Conversation.insert_many(histories).execute()
		
	def setTimeSynchronizeHistory(self):
		try:
			while 1:
				print("正在同步信息...")
				self.synchronizeChatHistory()
				time.sleep(30)
		except:
			print("同步消息失效!")
			traceback.print_exc()
		
	def getCookiesFromDB(self):
		'''
		提取该用户已保存的cookies(若存在)
		:return: Bool: 该用户是否存在已保存的cookies
		'''
		a = User.select().where(User.username == self.username).execute()[0]
		cookies = a.cookies
		flag = False
		if not cookies:
			pass
		elif "{" in cookies and "}" in cookies:
			print("正在调用已保存的cookie")
			cookies = json.loads(cookies)
			for i in cookies:
				if i == "hf-chat":
					flag = True
				self.cookies.set(i, cookies[i])
		return flag
	
	def init(self):
		'''
		Open-Assistant接口初始化总方法：
		1. 数据库中提取已保存cookies
		2. 提取已有对话
		3. 同步对话
		:return: 无
		'''
		self.getCookiesFromDB()
		res = self.requestsGet(self.url_index)
		# res = requests.get(self.url_index, headers=self.headers, cookies=self.cookies, proxies=self.proxies)
		# print(res)
		html = res.text
		cookies = res.cookies
		self.getConversations(html)
		# self.refreshCookies(cookies)
		Thread(target=self.setTimeSynchronizeHistory, daemon=True).start()
		# self.synchronizeChatHistory()
		
		
	def getReply(self, conversation, text):
		'''
		对话入口
		:param conversation: conversation_id
		:param text: 语句
		:return: 回复(使用流获取但并不以流形式返回)
		'''
		url = self.url_initConversation + f"/{conversation}"
		# res = self.requestsPost(url, stream=True, data=json.dumps(self.getData(text), ensure_ascii=False))
		reply = None
		def parseData(res:requests.Response):
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
						except:
							print(js)
			return reply
		for i in range(3):
			res = self.requestsPost(url, stream=True, data=json.dumps(self.getData(text), ensure_ascii=False))
			reply = parseData(res)
			if reply != None:
				break
		# res = requests.post(url, headers=self.headers, data=json.dumps(self.getData(text), ensure_ascii=False), proxies=self.proxies)
		if reply == None:
			raise Exception("No reply")
		# js = res.json()
		# reply = ""
		# for i in js:
		# 	reply += i["generated_text"]
		return reply
	
	def tranlate(self, text):
		'''
		将回复的英文翻译为英文，接口为有道
		:param text:  英文文本
		:return: 中文文本
		'''
		text = self.tranlater.translate(text)
		return text
	
	def chat(self, conversation, text):
		'''
		外都对话接口
		:param conversation: conversation_id
		:param text: 文本
		:return: (英文文本, 中文文本)
		'''
		eng = self.getReply(conversation, text)
		if len(re.findall("[a-zA-Z]", eng)) > 0:
			zh = self.tranlate(eng)
		else:
			zh = eng
		# Thread(target=)
		return (eng, zh)

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
	
	def saveChat(self, conversation_id, texts, is_user, text_id):
		Conversation.insert({
			Conversation.username: self.username,
			Conversation.conversation_id: conversation_id,
			Conversation.is_user: is_user,
			Conversation.text_eng: texts[0],
			Conversation.text_zh: texts[1],
			Conversation.time: self.getTime(),
			Conversation.text_id: text_id,
		})
		

def main():
	'''
	测试
	:return:
	'''
	openassistant = OpenAssistant("test", Translater.Translater())
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
	chat_history = openassistant.getHistories(conversation_id=conversation_id)
	for c in chat_history:
		text: str = c.text_eng if not c.text_zh else c.text_zh
		text.replace("\n","\\n")
		hist = f"({'user' if c.is_user else 'assist'}): {text}"
		print(hist)
	while 1:
		text = input("(user): ")
		if text == "#eng":
			if conversation:
				print(f"(assist): {conversation[0]}")
				continue
		conversation = openassistant.chat(conversation_id, text)
		print(f"(assist): {conversation[1]}")
	
		
if __name__ == "__main__":
	main()
		
