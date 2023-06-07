import argparse
import gc
import getpass
import json
import logging
import os
import time
import traceback
from threading import Thread
from websocket import WebSocketApp
from typing import List
from rich.console import Console
from rich.markdown import Markdown

from HuggingChat.OpenAssistant import OpenAssistant
from HuggingChat.Login import Login
from YDTranslate.Translater import Translater

EMAIL = "2134692955@qq.com"
PASSWD = ""

FLAG = False
LAST_STATEMENT = None
WEB_SEARCH = False
WSA = None
WSA_OPEN = False
CONSOLE = Console()

logging.getLogger().setLevel(logging.INFO)


def color(string, color: str):
	dic = {
		'white': '\033[30m',
		'red': '\033[31m',
		'green': '\033[32m',
		'yellow': '\033[33m',
		'blue': '\033[34m',
		'purple': '\033[35m',
		'cyan': '\033[36m',
		'black': '\033[37m'
	}
	return dic[color] + string + '\033[0m'


def checkCookies(u):
	login = Login(u, None)
	try:
		login.loadCookies()
		return True
	except Exception as e:
		# print(e)
		return False


def login(u, p=None, mysql=False, force=False):
	if not p:
		logging.info(f"No Password input, trying to load it from mysql or files\n无密码输入，尝试从mysql或文件中读取")
		login = Login(u, mysql=mysql)
		cookies = login.loadCookies()
	else:
		login = Login(u, p, mysql=mysql)
		if not force:
			try:
				cookies = login.loadCookies()
			except:
				cookies = login.main()
		else:
			cookies = login.main()
	return cookies


def updateMSG(js):
	global FLAG
	global LAST_STATEMENT
	status = js["status"]  # status stands for whether the message complete or still generating.
	msg = js["msg"]  # message it self with 'Typing...'.
	user = js["user"]  # whether this message is sent by user or claude.
	if status:
		string = f"({color(user, 'green' if user == 'user' else 'blue')}): {msg}"
		try:
			markdown = Markdown(string)
			CONSOLE.print(markdown)
		except:
			print(string)
		if user == "Open-Assistant":
			FLAG = False
	else:
		LAST_STATEMENT = msg


def updateWebSearch(js):
	print(js)


# string = f"Web Search: {js['type']} - {js['message']}"
# print(string)

def startWSApp(url):
	global WSA
	
	def on_open(wsapp):
		global WSA_OPEN
		WSA_OPEN = True
	def on_message(wsapp, data):
		data = json.loads(data)
		type = data["type"]
		if type == "text":
			updateMSG(data)
		if type == "web_search":
			updateWebSearch(data)
		elif type == "error":
			print("error occurred: ", data["msg"])
	
	WSA = WebSocketApp(url, on_message=on_message, on_open=on_open)
	Thread(target=WSA.run_forever, daemon=True).start()


def printOutHistories(histories: List[dict]):
	print(f"\n====== Histories of <{histories[0]['conversation_id'] if len(histories) > 1 else ''}> ======\n")
	string = ""
	for i in histories:
		string += f"({color('user', 'green') if i['is_user'] else color('Open-Assistant', 'blue')}): {i['text']}\n"
	string += "\n"
	print(string)


def changeWeb_search():
	global WEB_SEARCH
	WEB_SEARCH = True if not WEB_SEARCH else False
	print(f"WEB_SEARCH is set to `{WEB_SEARCH}`")


def newConversation(openassistant):
	global FLAG
	print("Input the first message you want to send (use `/exit` to get back): \n输入创建对话的第一个消息 (使用`/exit`退出新建对话): ")
	while 1:
		text = openassistant.getTextFromInput("(new) ")
		if text == "/exit":
			print("break.")
			break
		if text == "/web":
			changeWeb_search()
			continue
		FLAG = True
		title = openassistant.createConversation(text, WEB_SEARCH)
		print(f"Title: {title}")
		break


def main():
	global FLAG
	global WEB_SEARCH
	global WSA
	global WSA_OPEN
	
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"-u",
		type=str,
		help="登录邮箱(没账号请先注册一个) - email to be sign in.(sign up before this)"
	)
	parser.add_argument(
		"-p",
		action="store_true",
		help="再终端中输入密码(每账号请先注册一个) - input password in terminal(sign up before this)"
	)
	parser.add_argument(
		"--mysql",
		action="store_true",
		help="连接mysql保存用户名密码和同步历史对话消息 - use mysql to store conversation histories and cookies"
	)
	parser.add_argument(
		"-f",
		action="store_true",
		help="忽视已保存信息强制登录 - ignore the stored cookies and login"
	)
	args = parser.parse_args()
	u = EMAIL if not args.u else args.u
	print(f"Login in as <{u}>")
	if args.p:
		p = getpass.getpass()
	elif not checkCookies(u):
		p = getpass.getpass() if not PASSWD else PASSWD
	else:
		p = None
	mysql = args.mysql
	force = args.f
	
	cookies = login(u, p, mysql, force)
	print(f"You are now logged in as <{u}>")
	openassistant = OpenAssistant(u, cookies=cookies, tranlater=Translater(), mysql=mysql)
	openassistant.init()
	startWSApp(openassistant.wsurl)
	gc.collect()
	while not WSA_OPEN:
		time.sleep(0.1)
		continue
	while 1:
		try:
			gc.collect()
			while FLAG:
				time.sleep(0.1)
				continue
			text = openassistant.getTextFromInput()
			command = text.strip()
			if command[0] == "/":
				command = command[1:].split(" ")
				if command[0] == "exit":
					os._exit(0)
				elif command[0] == "new":
					newConversation(openassistant)
				elif command[0] == "ls":
					print(openassistant.printOutConversations())
				elif command[0] == "cd":
					try:
						openassistant.switchConversation(int(command[1]))
					except:
						print("cd fatal")
				elif command[0] == "rm":
					try:
						openassistant.removeConversation(int(command[1]))
					except:
						print("remove conversation fatal")
				elif command[0] == "old":
					printOutHistories(openassistant.getHistoriesByID())
				elif command[0] == "web":
					changeWeb_search()
				elif command[0] == "eng":
					if LAST_STATEMENT:
						openassistant.WSOut.sendMessage(status=True, user="Open-Assistant", msg=LAST_STATEMENT, conversation_id=openassistant.current_conversation)
						FLAG = True
					else:
						print("No reply yet.\n暂无回复")
				else:
					print("wrong command.\n错误命令")
					continue
			else:
				if not openassistant.current_conversation:
					print("Please select or create a conversation using '/ls' and '/cd <int>' or '/new'.\n请使用 '/ls' 和 '/cd <int>' 或 '/new' 来进入或创建新对话")
					continue
				if WEB_SEARCH:
					openassistant.chatWeb(text)
				else:
					openassistant.chat(text)
				FLAG = True
		except Exception as e:
			traceback.print_exc()


if __name__ == "__main__":
	main()
