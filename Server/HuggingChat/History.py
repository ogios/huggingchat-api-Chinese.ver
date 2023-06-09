import time
import traceback
from threading import Thread


class History_SQL:
	def __init__(self, email, openAssistant):
		self.openAssistant = openAssistant
		self.email = email
		from HuggingChat.SQL import User, Conversation
		self.User = User
		self.Conversation = Conversation
		
		def loop():
			try:
				while 1:
					time.sleep(15)
					# print("正在同步信息...")
					self.synchronizeChatHistory()
			except:
				print("同步消息失效!")
				traceback.print_exc()
		self.synchronizeChatHistory()
		Thread(target=loop, daemon=True).start()
	
	def getHistoriesByID(self, conversation_id):
		'''
		Get conversation histories from database
		:return: [{
			"conversation_id"
			"is_user"
			"text"
			"text_eng"
			"text_id"
		}]
		'''
		histories = []
		pees = self.Conversation.select().where(self.Conversation.username == self.email and self.Conversation.conversation_id == conversation_id).execute()
		for i in pees:
			histories.append({
				"conversation_id": conversation_id,
				"is_user": i.is_user,
				"text": i.text_zh,
				"text_eng": i.text_eng,
				"text_id": i.text_id,
			})
		return histories
	
	def getHistoyTextId(self) -> list:
		'''
		Get every text's unique uuid
		:return: List[text_id]
		'''
		# histories:List[Conversation] = self.getHistories()
		histories = self.Conversation.select(self.Conversation.text_id).where(self.Conversation.username == self.email).execute()
		return [c.text_id for c in histories]
	
	def synchronizeChatHistory(self):
		'''
		request for every conversation's chat history
		:return: None
		'''
		
		histories = []
		existed_texts = self.getHistoyTextId()
		for i in self.openAssistant.conversations:
			url = self.openAssistant.url_initConversation + f"/{i['id']}/__data.json?x-sveltekit-invalidated=_1"
			res = self.openAssistant.requestsGet(url)
			if res.status_code != 200:
				print("synchronize chat history fatal")
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
								"username": self.email,
								"conversation_id": i["id"],
								"is_user": 1 if history[his["from"]] == "user" else 0,
								"text_eng": history[his["content"]],
								"text_zh": self.openAssistant.tranlate(history[his["content"]]) if history[his["from"]] != "user" else history[his["content"]],
								"time": self.openAssistant.getTime(),
								"text_id": history[his["id"]],
							})
		self.Conversation.insert_many(histories).execute()


class History:
	def __init__(self, email, openAssistant):
		self.openAssistant = openAssistant
		self.email = email
	
	def getHistoriesByID(self, conversation_id):
		'''
		
		:return: [{
			"conversation_id"
			"is_user"
			"text"
			"text_id"
		}]
		'''
		histories = []
		url = self.openAssistant.url_initConversation + f"/{conversation_id}/__data.json?x-sveltekit-invalidated=_1"
		res = self.openAssistant.requestsGet(url)
		if res.status_code != 200:
			return None
		data = res.json()["nodes"]
		history = None
		for dic in data:
			if dic.__contains__("data"):
				history = dic["data"]
		if history:
			for his in history:
				if isinstance(his, dict):
					if his.__contains__("content"):
						histories.append({
							"conversation_id": conversation_id,
							"is_user": 1 if history[his["from"]] == "user" else 0,
							"text": history[his["content"]],
							"text_id": history[his["id"]],
						})
		return histories
