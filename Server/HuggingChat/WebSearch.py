import json
import logging
import traceback
import pycurl


def dictToString(cookies: dict):
	cookie = ""
	for i in cookies:
		cookie += f"{i}={cookies[i]}; "
	return cookie


class WebSearch:
	def __init__(self, url: str, cookies: dict, WSOut, conversation_id: str):
		self.data = None
		self.url = url
		self.cookies = cookies
		self.conversation_id = conversation_id
		self.WSOut = WSOut
		self.index = -1
		self.c = pycurl.Curl()
	
	def parseData(self, data):
		try:
			data = data.decode("utf-8")
			js = json.loads(data)
			self.data = js
			messages = js["messages"]
		except Exception as e:
			logging.error("One error occurred when parsing WebSearch data, it's fine since it sometimes returns responses in a wrong json format")
			# logging.error("WebSearch error:" + data)
			# traceback.print_exc()
			return
		if messages[-1]["type"] == "result":
			self.WSOut.sendWebSearch(messages[-1], conversation_id=self.conversation_id)
			return 456
		elif len(messages) - 1 > self.index:
			if self.index == -1:
				self.WSOut.sendWebSearch(messages[0], conversation_id=self.conversation_id)
				self.index = 0
			for message in messages[self.index + 1:]:
				self.WSOut.sendWebSearch(message, conversation_id=self.conversation_id)
				self.index += 1
	
	def getWebSearch(self):
		
		self.c.setopt(pycurl.URL, self.url)
		self.c.setopt(pycurl.REFERER, self.url)
		self.c.setopt(pycurl.HTTPHEADER, [
			'Connection: close', 'Cache-Control: max-age=0',
			'Accept: */*',
			'User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36',
			'Accept-Language: zh-CN,zh;q=0.8'
		])
		self.c.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_0)
		self.c.setopt(pycurl.COOKIE, dictToString(self.cookies))
		# self.c.setopt(pycurl.VERBOSE, True)
		self.c.setopt(pycurl.WRITEFUNCTION, self.parseData)
		try:
			self.c.perform()
		except Exception as e:
			if e.args[0] != 23:
				traceback.print_exc()
		self.c.close()
		return self.data


if __name__ == "__main__":
	pass
