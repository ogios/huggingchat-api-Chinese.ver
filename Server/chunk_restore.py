import requests
import os
import re

from typing import List

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


def getFileLength(l: list):
	indexes = []
	filenames = []
	n = 0
	for i in l:
		if not NAME in i:
			continue
		indexes.append((n, len(i)))
		filenames.append(i)
		n += 1
	return indexes, filenames


def sortByLength(indexs: List[tuple]):
	while 1:
		flag = False
		for i in range(len(indexs)):
			if i == len(indexs) - 1:
				break
			if indexs[i][1] > indexs[i + 1][1]:
				flag = True
				tmp = indexs[i]
				indexs[i] = indexs[i + 1]
				indexs[i + 1] = tmp
		if not flag:
			break
	return indexs


def getBackup():
	path = PATH + "/backup"
	if not os.path.exists(path):
		raise Exception(f"{path} not exist")
	files = os.listdir(path)
	indexes, files = getFileLength(files)
	indexes = sortByLength(indexes)
	name = files[indexes[-1][0]]
	return path + f"/{name}"


def restoreChunck(path):
	print(f"Restore using {path}...")
	with open(path, "r") as f:
		scr = f.read()
	if scr:
		try:
			with open(PATH_TO_MODELS + f"/{NAME}", "w") as f:
				f.write(scr)
		except Exception as e:
			print(e)
			with open(PATH_TO_MODELS + f"/{NAME}", "w", encoding="utf-8") as f:
				f.write(scr)
	else:
		print(f"Nothing is in this file: {path}")


script = getBackup()
print(script)
restoreChunck(script)

print(color(
	"Warning: this operation may cause something bad to your `requests` module.\n" + \
	"if it really does, please reinstall it using `pip3 uninstall requests` and `pip3 install requests`.",
	"red"
))
