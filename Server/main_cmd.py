import argparse
import gc
import getpass
import json
import logging
import os
import sys
import time
import traceback
from threading import Thread
from websocket import WebSocketApp

from HuggingChat.OpenAssistant import OpenAssistant
from HuggingChat.Login import Login
from YDTranslate.Translater import Translater

EMAIL = ""
PASSWD = ""

FLAG = False
LAST_STATEMENT = None
WEB_SEARCH = False

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


def login(u, p=None, mysql=False, force=False):
	if not p:
		logging.debug(f"No Password input, trying to load it from mysql or files")
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
		print(f"({color(user, 'green' if user == 'user' else 'blue')}): {msg}")
		if user == "Open-Assistant":
			FLAG = False
	else:
		LAST_STATEMENT = msg

def updateWebSearch(js):
	print(js)
	# string = f"Web Search: {js['type']} - {js['message']}"
	# print(string)

def startWSApp(url):
	def on_message(wsapp, data):
		data = json.loads(data)
		type = data["type"]
		if type == "text":
			updateMSG(data)
		if type == "web_search":
			updateWebSearch(data)
		elif type == "error":
			print("error occurred: ", data["msg"])
	
	wsa = WebSocketApp(url, on_message=on_message)
	Thread(target=wsa.run_forever, daemon=True).start()


def printOutHistories(histories: list[dict]):
	print(f"\n====== Histories of <{histories[0]['conversation_id'] if len(histories) > 1 else ''}> ======\n")
	string = ""
	for i in histories:
		string += f"({color('user', 'green') if i['is_user'] else color('Open-Assistant', 'blue')}): {i['text']}\n"
	string += "\n"
	print(string)


def main():
	global FLAG
	global WEB_SEARCH
	
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"-u",
		type=str,
		help="email to be sign in.(sign up before this)"
	)
	parser.add_argument(
		"-p",
		action="store_true",
		help="input password in terminal(sign up before this)"
	)
	parser.add_argument(
		"--mysql",
		action="store_true",
		help="use mysql to store conversation histories and cookies or simple json file"
	)
	parser.add_argument(
		"-f",
		action="store_true",
	)
	args = parser.parse_args()
	u = EMAIL if not args.u else args.u
	if args.p:
		p = getpass.getpass()
	else:
		p = getpass.getpass() if not PASSWD else PASSWD
	mysql = args.mysql
	force = args.f
	
	cookies = login(u, p, mysql, force)
	print(f"you are now sign in as '{u}'")
	openassistant = OpenAssistant(u, cookies=cookies, tranlater=Translater(), mysql=mysql)
	openassistant.init()
	startWSApp(openassistant.wsurl)
	gc.collect()
	while 1:
		try:
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
					print("Input the first message you want to send: ")
					text = openassistant.getTextFromInput()
					if text == "/exit":
						print("break.")
						continue
					FLAG = True
					title = openassistant.createConversation(text, WEB_SEARCH)
					print(f"Title: {title}")
				elif command[0] == "ls":
					print(openassistant.printOutConversations())
				elif command[0] == "cd":
					try:
						openassistant.switchConversation(int(command[1]))
					except:
						print("cd fatal")
				elif command[0] == "old":
					printOutHistories(openassistant.getHistoriesByID())
				elif command[0] == "web":
					WEB_SEARCH = True if not WEB_SEARCH else False
					print(f"WEB_SEARCH is set to `{WEB_SEARCH}`")
				else:
					print("wrong command.")
					continue
			else:
				if not openassistant.current_conversation:
					print("Please select or create a conversation using '/ls' and '/cd <int>' or '/new'")
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
