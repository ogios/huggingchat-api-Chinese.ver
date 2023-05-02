import hashlib
import json
import time
from YDTranslate import YDDeocder
import requests
import requests.utils
import random


def getMD5(text: str):
	return hashlib.md5(text.encode("UTF-8"))


class Translater:
	def __init__(self, hot=True):
		self.key_url = "https://dict.youdao.com/webtranslate/key"
		self.transalte_url = "https://dict.youdao.com/webtranslate"
		self.rlog_url = "https://rlogs.youdao.com/rlog.php"
		self.decoder = YDDeocder.YouDaoDecoder()
		self.key = "fsdsogkndfokasodnaso"
		self.data = {
			"i": None,
			"from": "en",
			"to": "zh-CHS",
			"domain": "0",
			"dictResult": "true",
			"keyid": "webfanyi",
			"sign": None,
			"client": "fanyideskweb",
			"product": "webfanyi",
			"appVersion": "1.0.0",
			"vendor": "web",
			"pointParam": "client,mysticTime,product",
			"mysticTime": None,
			"keyfrom": "fanyi.web",
		}
		self.headers = {
			"Accept": "application/json, text/plain, */*",
			"Accept-Encoding": "gzip, deflate, br",
			"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
			"DNT": "1",
			"Pragma": "no-cache",
			"Referer": "https://fanyi.youdao.com/",
			"Sec-Fetch-Dest": "empty",
			"Sec-Fetch-Mode": "cors",
			"Sec-Fetch-Site": "same-site",
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.58",
		}
		self.cookies: requests.utils.RequestsCookieJar = requests.utils.cookiejar_from_dict({})
		if hot == True:
			print("不获取USER_ID与key, 使用默认设置, 若出现报错可能会是因为默认设置过期需要更新等原因")
			self.cookies.set("OUTFOX_SEARCH_USER_ID", "57246213@50.7.59.85")
			self.key = "fsdsogkndfokasodnaso"
		else:
			print("正在获取USER_ID...")
			self.getUserID()
			print("done.")
			print("正在获取key...")
			self.getKey()
			print("done.")
	
	def getUserID(self):
		noco = str(2147483647 * random.random())
		params = {
			"_npid": "fanyiweb",
			"_ncat": "pageview",
			"_ncoo": f"{noco}",
			"_nssn": "NULL",
			"_nver": "1.2.0",
			"_ntms": f"{int(time.time() * 1000)}",
			"_nref": "http://fanyi.youdao.com/",
			"_nurl": "https://fanyi.youdao.com/index.html#/",
			"_nres": "1536x864",
			"_nlmf": "1682590851",
			"_njve": "0",
			"_nchr": "utf-8",
			"_nfrg": "/",
			"/": "NULL",
			"screen": "1536*864",
		}
		self.cookies.set("OUTFOX_SEARCH_USER_ID_NCOO", noco)
		res = requests.get(self.rlog_url, params=params, headers=self.headers, cookies=self.cookies)
		# print(res)
		# print(res.cookies)
		cookies = res.cookies.get_dict()
		for i in cookies:
			if i == "OUTFOX_SEARCH_USER_ID":
				self.cookies.set(i, cookies["OUTFOX_SEARCH_USER_ID"])
	
	def getKey(self):
		tp = int(time.time() * 1000)
		string = f"client={self.data['client']}&mysticTime={tp}&product={self.data['product']}&key={'asdjnjfenknafdfsdfsd'}"
		sign = getMD5(string).hexdigest()
		params = {
			"keyid": "webfanyi-key-getter",
			"sign": f"{sign}",
			"client": "fanyideskweb",
			"product": "webfanyi",
			"appVersion": "1.0.0",
			"vendor": "web",
			"pointParam": "client,mysticTime,product",
			"mysticTime": f"{tp}",
			"keyfrom": "fanyi.web",
		}
		url = f"?keyid=webfanyi-key-getter&sign={sign}&client=fanyideskweb&product=webfanyi&appVersion=1.0.0&vendor=web&pointParam=client,mysticTime,product&mysticTime={tp}&keyfrom=fanyi.web"
		res = requests.get(self.key_url + url, headers=self.headers, cookies=self.cookies)
		js = res.json()
		# print(res)
		# print(js)
		if js["msg"] == "OK":
			self.key = js["data"]["secretKey"]
		else:
			raise Exception("key lose")
	
	def translate(self, text):
		tp = int(time.time() * 1000)
		string = f"client={self.data['client']}&mysticTime={tp}&product={self.data['product']}&key={self.key}"
		sign = getMD5(string).hexdigest()
		self.data["sign"] = sign
		self.data["i"] = text
		self.data["mysticTime"] = str(tp)
		res = requests.post(self.transalte_url, data=self.data, headers=self.headers, cookies=self.cookies)
		# print(res)
		if res.status_code != 200:
			raise Exception("translate fatal")
		text = res.text
		# print(text)
		decoded = self.decoder.decode(text)
		# print(decoded)
		translated = self.getResult(json.loads(decoded))
		if not translated:
			raise Exception("translate fatal")
		return translated
	
	def getResult(self, js):
		if js["code"] == 0:
			string = ""
			for i in js["translateResult"]:
				for s in i:
					string += s["tgt"]
			return string
		else:
			return None


if __name__ == "__main__":
	translate = Translater()
	c = translate.translate("Certainly! I can try my best to respond in Chinese if that would make things easier for you. Would you like me to provide you with some tips on learning Chinese? Or perhaps translate something specific into Chinese for you? Let me know how I can assist you.")
	print(c)
