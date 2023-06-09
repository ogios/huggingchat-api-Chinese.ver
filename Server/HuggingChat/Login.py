import logging
import os
import re
import requests

import requests.utils
import requests.sessions
import json


class Login:
	def __init__(self, email: str, passwd: str=None, mysql: bool=False) -> None:
		self.email: str = email
		self.passwd: str = passwd
		self.headers = {
			"Referer": "https://huggingface.co/",
			# "Content-Type": "application/json",
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.64",
		}
		# self.proxies = {
		# 	"http": "http://127.0.0.1:7890",
		# 	"https": "http://127.0.0.1:7890"
		# }
		self.cookies = requests.sessions.RequestsCookieJar()
		self.mysql = mysql
		if self.mysql:
			from .SQL import User, Conversation
			self.User = User
			self.Conversation = Conversation
			user = User.select().where(
				User.email == self.email
			).execute()
			# if len(user) == 0:
			# 	User.insert({
			# 		User.email: self.email,
			# 		User.passwd: self.passwd,
			# 	}).execute()
			# else:
			# 	if self.passwd:
			# 		User.update({
			# 			User.passwd: self.passwd
			# 		}).where(User.email == self.email).execute()
		else:
			self.COOKIE_DIR = os.path.dirname(os.path.abspath(__file__)) + "/usercookies"
			self.COOKIE_PATH = self.COOKIE_DIR + f"/{self.email}.json"
			if not os.path.exists(self.COOKIE_DIR):
				logging.info("Cookie directory not found, creating...")
				os.makedirs(self.COOKIE_DIR)
			logging.info(f"Cookie store path: {self.COOKIE_PATH}")
		
	def requestsGet(self, url:str, params=None, allow_redirects=True) -> requests.Response:
		res = requests.get(
			url,
			params=params, 
			headers=self.headers, 
			cookies=self.cookies, 
			# proxies=self.proxies,
			allow_redirects=allow_redirects,
			)
		# if res.status_code == 200:
		self.refreshCookies(res.cookies)
		return res
	
	def requestsPost(self, url:str, headers=None, params=None, data=None, stream=False, allow_redirects=True) -> requests.Response:
		res = requests.post(
			url,
			stream=stream, 
			params=params, 
			data=data, 
			headers=self.headers if headers == None else headers, 
			cookies=self.cookies, 
			# proxies=self.proxies,
			allow_redirects=allow_redirects
			)
		# if allow_redirects and res.status_code == 200:
		self.refreshCookies(res.cookies)
		return res
				
	def refreshCookies(self, cookies: requests.sessions.RequestsCookieJar):
		dic = cookies.get_dict()
		for i in dic:
			self.cookies.set(i, dic[i])

	def SigninWithEmail(self):
		url = "https://huggingface.co/login"
		data = {
			"username": self.email,
			"password": self.passwd,
		}
		res = self.requestsPost(url=url, data=data, allow_redirects=False)
		if res.status_code == 400:
			raise Exception("Incorrect username or password\n用户名或密码错误")

	def getAuthURL(self) -> str:
		url = "https://huggingface.co/chat/login"
		headers = {
			"Referer": "https://huggingface.co/chat/login",
			"User-Agent": self.headers["User-Agent"],
			"Content-Type": "application/x-www-form-urlencoded"
		}
		res = self.requestsPost(url, headers=headers, allow_redirects=False)
		if res.status_code == 200:
			# location = res.headers.get("Location", None)
			location = res.json()["location"]
			if location:
				return location
			else:
				raise Exception("No authorize url!")
		else:
			raise Exception("Something went wrong!")
	
	def grantAuth(self, url: str) -> int:
		res = self.requestsGet(url)
		if res.status_code != 200:
			raise Exception("grant auth fatal!")
		csrf = re.findall('/oauth/authorize.*?name="csrf" value="(.*?)"', res.text)
		if len(csrf) == 0:
			raise Exception("No csrf found!")
		data = {
			"csrf":csrf[0]
		}

		res = self.requestsPost(url, data=data, allow_redirects=False)
		if res.status_code != 303:
			raise Exception(f"get hf-chat cookies fatal! - {res.status_code}")
		else:
			location = res.headers.get("Location")
		res = self.requestsGet(location, allow_redirects=False)
		if res.status_code != 302:
			raise Exception(f"get hf-chat cookie fatal! - {res.status_code}")
		else:
			return 1
	
	# def checkIfAlone(self) -> int:
	# 	users = self.User.select().execute()
	# 	return 1 if len(users) == 1 else 0
	
	# def checkIfCookieExist(self) -> int:
	# 	if self.mysql:
	# 		users = self.User.select().where(
	# 			self.User.email == self.email
	# 		).execute()
	# 		if len(users) == 1:
	# 			try:
	# 				self.cookies = json.loads(users[0].cookies)
	# 				return 1
	# 			except:
	# 				return 0
	# 	else:
	# 		raise Exception("can")
			
	def saveCookies(self):
		if self.mysql:
			users = self.User.select().where(
				self.User.email == self.email
			).execute()
			if len(users) != 0:
				self.User.update({
					self.User.passwd: self.passwd,
					self.User.cookies: json.dumps(self.cookies.get_dict(), ensure_ascii=True)
				}).where(self.User.email == self.email).execute()
			else:
				self.User.insert({
					self.User.email: self.email,
					self.User.passwd: self.passwd,
					self.User.cookies: json.dumps(self.cookies.get_dict(), ensure_ascii=True)
				}).execute()
				
		else:
			with open(self.COOKIE_PATH, "w", encoding="utf-8") as f:
				f.write(json.dumps(self.cookies.get_dict()))
			return self.COOKIE_PATH
	
	def loadCookies(self):
		if self.mysql:
			users = self.User.select().where(
				self.User.email == self.email
			).execute()
			if len(users) == 1:
				try:
					self.cookies = json.loads(users[0].cookies)
					return self.cookies
				except:
					raise Exception("cookie for this user if haven't been saved")
			else:
				raise Exception("user not exist")
		else:
			if os.path.exists(self.COOKIE_PATH):
				with open(self.COOKIE_PATH, "r", encoding="utf-8") as f:
					try:
						js = json.loads(f.read())
						for i in js.keys():
							self.cookies.set(i, js[i])
							logging.info(f"{i} loaded")
						return self.cookies
					except:
						raise Exception("load cookies from files fatal.")
			else:
				raise Exception(f"{self.COOKIE_PATH} not exist")
	
	def main(self):
		self.SigninWithEmail()
		location = self.getAuthURL()
		if self.grantAuth(location):
			print("done")
		self.saveCookies()
		return self.loadCookies()
		
	
if __name__ == "__main__":
	email = ""
	passwd = ""
	log = Login(email, passwd)
	log.main()
