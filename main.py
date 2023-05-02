# from TestArea import CustomizedKEYS
import math
import sys
from threading import Thread

import _curses
import curses
import curses.textpad
from OpenAssistant import OpenAssistant
from YDTranslate import Translater
from utils import CustomizedKEYS


class CMDOutput:
	def __init__(self, output_win: _curses.window):
		self.output_win = output_win
		self.output_win_hw = output_win.getmaxyx()
		self.output_win_pos = output_win.getbegyx()
		self.text_hw = (self.output_win_hw[0] - 3, self.output_win_hw[1] - 2)
		self.output_win.refresh()
		self.lines = []
		self.maxlines = self.text_hw[0]
		self.position_begin = 2
		self.position_end = self.maxlines + self.position_begin
		# self.test()
	
	def test(self):
		text = ""
		for i in range(50):
			for a in range(26):
				text += chr(67 + a)
		self.print(text, is_user=True)
	
	def toLines(self, text):
		lines = []
		paragraphs = text.split("\n")
		for i in paragraphs:
			col = len(i) / self.text_hw[1]
			line = []
			if col > 0:
				for c in range(math.ceil(col)):
					line.append(i[c * self.text_hw[1]:(c + 1) * self.text_hw[1]])
			lines.extend(line)
		return lines
	
	def _print(self, text):
		lines = self.toLines(text)
		# print(f"lines: {lines}")
		self.lines.extend(lines)
		self.lines = self.lines[-self.maxlines:]
		position_begin = 2
		self.initOutput(self.output_win)
		for line in self.lines:
			self.output_win.addstr(position_begin, 1, line)
			position_begin += 1
		x = self.output_win.getyx()[1]
		self.output_win.refresh()
	
	def print(self, text: str, is_user: bool):
		text = f"({'user' if is_user else 'assist'}): " + text
		self._print(text)
	
	def initOutput(self, output_win):
		output_win.clear()
		# output_win.border()
		output_win.attron(curses.color_pair(1))
		output_win.addstr(1, 1, "Output:")
		output_win.attroff(curses.color_pair(1))
		output_win.refresh()


def main(stdscr: _curses.window, assistant:OpenAssistant.OpenAssistant, conversation_id:str):
	# 初始化curses
	curses.curs_set(1)
	# curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
	curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_CYAN)
	height, width = stdscr.getmaxyx()
	
	# 创建输出框
	def initOutput(output_win):
		output_win.clear()
		# output_win.border()
		output_win.attron(curses.color_pair(1))
		output_win.addstr(1, 1, "Output:")
		output_win.attroff(curses.color_pair(1))
		# output_win.addstr(f" {height}x{width}\n")
		output_win.refresh()
	
	output_win = curses.newwin(height - 6, width - 2, 1, 1)
	initOutput(output_win)
	
	# 创建输入框
	def initInput(input_win):
		input_win.clear()
		input_win.border()
		input_win.attron(curses.color_pair(1))
		input_win.addstr(1, 1, "Input: ")
		input_win.attroff(curses.color_pair(1))
		input_win.refresh()
	
	input_win = curses.newwin(3, width - 2, height - 4, 1)
	initInput(input_win)
	input_win.keypad(True)
	
	def getInput(input_win):
		text = ""
		initInput(input_win)
		while 1:
			c = input_win.getch()
			if c == CustomizedKEYS.KEY_ESC:
				return None
			elif c == CustomizedKEYS.KEY_ENTER:
				break
			elif c == CustomizedKEYS.KEY_BACKSPACE:
				text = text[:-1]
				initInput(input_win)
				input_win.addstr(text)
			else:
				text += chr(c)
				input_win.addstr(chr(c))
			input_win.refresh()
		initInput(input_win)
		return text
	
	def getHistory(assistant:OpenAssistant.OpenAssistant, conversation_id:str, output:CMDOutput):
		chat_history = assistant.getHistories(conversation_id=conversation_id)
		# print(f"chatHistory: {chat_history}")
		# print(f"count: {chat_history.count}")
		for c in chat_history:
			text: str = c.text_eng if not c.text_zh else c.text_zh
			text.replace("\n", "\\n")
			# print(f"text: {text}")
			output.print(text, is_user=c.is_user)

	
	output = CMDOutput(output_win)
	conversation=None
	if not conversation_id:
		text = getInput(input_win)
		if text == None:
			return
		output.print(text, is_user=True)
		conversation_detail = assistant.createConversation(text)
		conversation_id = conversation_detail[1]["id"]
		conversation = conversation_detail[0]
		output.print(conversation[1], is_user=False)
	else:
		print("Getting history...")
		getHistory(assistant, conversation_id, output)
		
	# 获取输入并在输出框中显示
	while 1:
		text = getInput(input_win)
		if text == None:
			return
		if text == "#eng":
			if conversation:
				text = conversation[0]
			else:
				text = "!还未开始对话"
			output.print(text, is_user=False)
			continue
		output.print(text, is_user=True)
		conversation = assistant.chat(conversation_id, text)
		output.print(conversation[1], is_user=False)


def initAssistant(username):
	tranlater = Translater.Translater(hot=True)
	assistant = OpenAssistant.OpenAssistant(username, tranlater)
	assistant.init()
	print("\n -数字选择对话，输入 '-1' 创建新对话")
	while 1:
		conversations = assistant.conversations
		print("已有的对话:")
		for i in range(len(conversations)):
			print(f"{i}. {conversations[i]['title']}")
		option = input(">>>")
		try:
			option = int(option)
		except:
			if option == "exit":
				sys.exit()
			continue
		if option == -1:
			conversation_id = None
		else:
			if (option >= 0) & (option <= len(conversations)-1):
				conversation_id = conversations[option]["id"]
			else:
				print("invalid input")
				continue
		curses.wrapper(main, assistant=assistant, conversation_id=conversation_id)
			
if __name__ == "__main__":
	initAssistant("test")

# curses.wrapper(main)