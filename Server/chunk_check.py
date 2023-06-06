import requests
import os
import re

PATH_TO_MODELS = os.path.dirname(requests.__file__)
PATH = os.path.dirname(os.path.abspath(__file__))
NAME = "models.py"


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


def getScript():
	path = PATH_TO_MODELS + f"/{NAME}"
	try:
		with open(path, "r") as f:
			script = f.read()
	except Exception as e:
		print(e)
		with open(path, "r", encoding="utf-8") as f:
			script = f.read()
	return script


def check(scr):
	print(f"Checking file state...")
	c = re.search("\n.*?(except ProtocolError as e:.*?)\n.*?(raise ChunkedEncodingError\(e\))", scr)
	print("------")
	print(c.group(0))
	print("------")



script = getScript()
check(script)
