import traceback

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


def backup(scr):
	print("Backing up...")
	path = PATH + "/backup"
	if not os.path.exists(path):
		os.makedirs(path)
	name = NAME
	while name in os.listdir(path):
		name = "_" + name
	
	with open(path + f"/{name}", "w") as f:
		f.write(scr)

def resolveChunck(scr):
	path = PATH_TO_MODELS + f"/{NAME}"
	print(f"updating file: {path}")
	c = re.search("\n.*?(.*?except ProtocolError as e:)\n.*?(.*?raise ChunkedEncodingError\(e\))", scr)
	print("------")
	print(c.group(0))
	print("------")
	# print(c.group(1))
	# print("------")
	# print(c.group(2))
	a = re.sub("\n.*?(.*?except ProtocolError as e:)\n.*?(.*?raise ChunkedEncodingError\(e\))", r"\n#\1 \n#\2", scr)
	with open(path, "w") as f:
		f.write(a)
	print(color("done.\nplease run chunk_check.py to check that file.", "green"))


script = getScript()
# backup(script)
try:
	resolveChunck(script)
	backup(script)
	print(color(
		"Warning: this operation may cause something bad to your `requests` module.\n" + \
		"if it really does, please reinstall it using `pip3 uninstall requests` and `pip3 install requests`.",
		"red"
	))
except:
	traceback.print_exc()
	print(color("it seems that you already done it.\nplease run chunk_check.py to check that file.", "green"))
	


