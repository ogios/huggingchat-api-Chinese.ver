import re
import requests
from OpenAssistant.SQL import User, Conversation
# from SQL import User
import requests.utils
import requests.sessions
import json


class Login:
	def __init__(self, email: str, passwd: str) -> None:
		self.email: str = email
		self.passwd: str = passwd
		user =  User.select().where(
			User.email == self.email
		).execute()
		if len(user) == 0:
			User.insert({
				User.email: self.email,
				User.passwd: self.passwd,
			}).execute()

		
		self.headers = {
			"Referer": "https://huggingface.co/",
			# "Content-Type": "application/json",
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.64",
		}
		self.proxies = {
			"http": "http://127.0.0.1:7890",
			"https": "http://127.0.0.1:7890"
		}
		self.cookies = requests.sessions.RequestsCookieJar()
		
	def requestsGet(self, url:str, params=None, allow_redirects=True) -> requests.Response:
		res = requests.get(
			url,
			params=params, 
			headers=self.headers, 
			cookies=self.cookies, 
			proxies=self.proxies,
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
			proxies=self.proxies,
			allow_redirects=allow_redirects
			)
		# if allow_redirects and res.status_code == 200:
		self.refreshCookies(res.cookies)
		return res
				
	def refreshCookies(self, cookies:requests.sessions.RequestsCookieJar):
		dic = cookies.get_dict()
		for i in dic:
			self.cookies.set(i, dic[i])
		User.update({
			User.cookies: json.dumps(self.cookies.get_dict(), ensure_ascii=True)
		}).where(User.email == self.email).execute()

	def SigninWithEmail(self):
		url = "https://huggingface.co/login"
		data = {
			"username": self.email,
			"password": self.passwd,
		}
		res = self.requestsPost(url=url, data=data, allow_redirects=False)
		if res.status_code == 400:
			raise Exception("用户名或密码错误")

	def getAuthURL(self) -> str | None:
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
	
	def main(self):
		self.SigninWithEmail()
		location = self.getAuthURL()
		if self.grantAuth(location):
			print("done")
	
if __name__ == "__main__":

	log = Login(email, passwd)
	log.main()
