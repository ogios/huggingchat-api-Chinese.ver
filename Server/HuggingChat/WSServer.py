import json
import logging
import random
import socket
import time
from threading import Thread

from websocket_server import WebsocketServer, WebSocketHandler


def try_port(port):
	"""获取可用的端口"""
	tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		tcp.bind(("", port))
		_, port = tcp.getsockname()
		tcp.close()
		return 1
	except Exception as e:
		print(e)
		return 0


def getRandomPort():
	while 1:
		port = random.randint(49152, 65535)
		if try_port(port):
			return port


def get_free_tcp_port():
	"""获取可用的端口"""
	tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tcp.bind(("", 0))
	_, port = tcp.getsockname()
	tcp.close()
	return port


class WSOut:
	def __init__(self, host="127.0.0.1", port: int = None):
		self.IP_PORT: int = port if port != None else getRandomPort()
		self.IP_ADDR: str = "0.0.0.0"
		self.host = host
		self.server: WebsocketServer = None
		self.message_list = []
		Thread(target=self._sendMessage, daemon=True).start()
		Thread(target=self.startWebsocketServer, daemon=True).start()
	
	def getUrl(self):
		return f"ws://{self.host}:{self.IP_PORT}"
	
	# def failureRequest(self, handler: WebSocketHandler, status=None, msg=None, type=""):
	# 	data = {
	# 		"ok": False,
	# 		"status": status,
	# 		"msg": msg,
	# 		"type": type
	# 	}
	# 	handler.send_message(json.dumps(data, ensure_ascii=False))
	
	# def successRequest(self, handler: WebSocketHandler, status=None, msg=None, type=""):
	# 	data = {
	# 		"ok": True,
	# 		"status": status,
	# 		"msg": msg,
	# 		"type": type
	# 	}
	# 	handler.send_message(json.dumps(data, ensure_ascii=False))
	
	def startWebsocketServer(self):
		# def on_open(client: dict, server: WebsocketServer):
		
		# def on_message(client: dict, server: WebsocketServer, msg):
		
		server = WebsocketServer(host=self.IP_ADDR, port=self.IP_PORT, loglevel=logging.INFO)
		
		# server.set_fn_new_client(on_open)
		# server.set_fn_message_received(on_message)
		self.server = server
		self.server.run_forever()
		self.server.server_close()
	
	def _sendMessage(self):
		while 1:
			if self.server:
				if len(self.server.clients) > 0:
					while len(self.message_list) > 0:
						self.server.send_message_to_all(self.message_list[0])
						del self.message_list[0]
			time.sleep(0.01)
	
	def sendMessage(self, status, msg, user, conversation_id):
		data = {
			"type": "text",
			"status": status,
			"msg": msg,
			"user": user,
			"conversation_id": conversation_id
		}
		self.message_list.append(json.dumps(data, ensure_ascii=False))
	
	def sendError(self, status=None, msg=None):
		data = {
			"type": "error",
			"status": status,
			"msg": msg,
		}
		self.message_list.append(json.dumps(data, ensure_ascii=False))
	
	def sendWebSearch(self, data: list, conversation_id):
		data = {
			"type": "web_search",
			"data": data,
			"conversation_id": conversation_id
		}
		self.message_list.append(json.dumps(data, ensure_ascii=False))
