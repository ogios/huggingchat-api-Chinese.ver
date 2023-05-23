import sys
from OpenAssistant.OpenAssistant import OpenAssistant
from OpenAssistant.Login import Login
from YDTranslate.Translater import Translater
from OpenAssistant.SQL import User
import click

def checkIfAlone() -> bool:
	users = User.select().execute()
	return 1 if len(users) == 1 else 0

def checkIfExist(email: str) -> bool:
	users = User.select().where(
		User.email == email
    ).execute()
	return 1 if len(users) == 1 else 0

def login(u, p):
	if u:
		if checkIfExist(u):
			print(f"user exist - {u}")
			return u
		else:
			passwd = input("no saved account match, password is needed to login:") if not p else p
			Login(u, passwd).main()
			return u
	else:
		print("no email input, detecting if there's only one account...")
		if checkIfAlone():
			u = User.get().email
			print("one email detected.")
			return u
		else:
			raise Exception("no input and multipul accounts in database, you must select one if there's not just one account")


@click.command()
@click.option("-u", default=None, help="email to be sign in.(sign up before this)")
@click.option("-p", default=None, help="password to be sign in.(sign up before this)")
def main(u=None, p=None):
	'''
	测试
	:return:
	'''
	u = login(u, p)
	print(f"you are now sign in as '{u}'")
	openassistant = OpenAssistant(u, Translater())
	openassistant.init()
	conversation = None
	conversation_detail = None
	conversations = openassistant.conversations
	print("* Conversations that have been established: (input index to start or '-1' to start a new one)")
	print()
	for i in range(len(conversations)):
		print(f"	{i}. {conversations[i]['title']}")
	print()
	while 1:
		try:
			option = input(">>>")
			if option == "exit":
				sys.exit()
			else:
				option = int(option)
			conversation_detail = None if option == -1 else conversations[option]
			break
		except:
			print("wrong input")
	if option == -1:
		print("start one conversation with the first chat.")
		text = input("(user): ")
		(conversation, conversation_detail) = openassistant.createConversation(text)
		# print(f"conversation_detail: {conversation_detail}")
		print(f"(assist): {conversation[1]}")
		# print(f"reply: {conversation[0]}", f"conversation_detail: {conversation[1]}", sep="\n")
		# conversation_detail = conversation[1]

	conversation_id = conversation_detail["id"]
	print(f"Title: {conversation_detail['title']}")
	chat_history = openassistant.getHistories(conversation_id=conversation_id)
	for c in chat_history:
		text: str = c.text_eng if not c.text_zh else c.text_zh
		text.replace("\n","\\n")
		hist = f"({'user' if c.is_user else 'assist'}): {text}"
		print(hist)
	while 1:
		text = input("(user): ")
		if text == "#eng":
			if conversation:
				print(f"(assist): {conversation[0]}")
				continue
		conversation = openassistant.chat(conversation_id, text)
		print(f"(assist): {conversation[1]}")
	
if __name__ == "__main__":
	main()