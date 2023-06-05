import gc
import json
import logging
import fastapi
from json.decoder import JSONDecodeError
from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread
from requests.sessions import RequestsCookieJar
from HuggingChat.OpenAssistant import OpenAssistant
from HuggingChat.Login import Login
from YDTranslate.Translater import Translater
from OAuthSupport.UserManagement import UserManagement

logging.getLogger().setLevel(logging.INFO)

app = fastapi.FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"]
)

SESSIONS = {}
UM = UserManagement()
TL = Translater()


@app.post("/init")
async def login(req: Request):
	global SESSIONS
	form = await req.form()
	email = form.get("email")
	enc_passwd = form.get("passwd")
	if not enc_passwd or not email:
		raise HTTPException(status_code=400, detail="Missing username or password")
	passwd = UM.decPass(enc_passwd)
	if not UM.checkUserExist(email, dec_passwd=passwd):
		sign = Login(email, passwd, mysql=False)
		try:
			cookies: RequestsCookieJar = sign.loadCookies()
			if not cookies.__contains__("hf-chat") or not cookies.__contains__("token"):
				raise Exception("Essential cookies' lost")
		except Exception as e:
			logging.debug(f"{e}. Load cookies for {email} fatal, logging in...")
			try:
				cookies: RequestsCookieJar = sign.main()
				if not cookies.__contains__("hf-chat") or not cookies.__contains__("token"):
					raise Exception("Essential cookies' lost")
			except:
				raise HTTPException(status_code=400, detail="login to huggingchat fatal. incorrect username or password")
		assistant = OpenAssistant(email, cookies, TL, mysql=False)
		assistant.init()
		SESSIONS[email] = assistant
		UM.addUser(email, passwd)
	return {"token": UM.getTokenByEmail(email), "ws": SESSIONS[email].wsurl}


@app.post("/sendMessage")
async def sendMessage(req: Request):
	# token = req.headers.get("token")
	# if not token or not UM.checkToken(token):
	# 	raise HTTPException(status_code=401, detail="Not Authorized")
	try:
		js: dict = await req.json()
		if not js.__contains__("text") or not js.__contains__("web"):
			raise HTTPException(status_code=400, detail="missing something")
		text = js["text"]
		web = js["web"]
		if not isinstance(text, str) or not isinstance(web, bool):
			raise HTTPException(status_code=400, detail="wrong format")
	except JSONDecodeError:
		raise HTTPException(status_code=400, detail="wrong format")
	
	print(text, web)

if __name__ == "__main__":
	import uvicorn
	
	uvicorn.run(app, host="0.0.0.0", port=5542)
