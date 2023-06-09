# import pymysql
import uuid
import peewee
import json
import os


def initDB():
	# global db
	PATH = os.path.dirname(__file__)
	with open(PATH + "/mysqlconf.json", "r") as f:
		sqlconfig = json.loads(f.read())
	return peewee.MySQLDatabase(
		sqlconfig["database"],
		user=sqlconfig["sqluser"],
		password=sqlconfig["sqlpass"],
		host=sqlconfig["host"],
		port=sqlconfig["port"]
	)


db = initDB()


class BaseModel(peewee.Model):
	class Meta:
		database = db


class User(BaseModel):
	email = peewee.CharField(primary_key=True)
	passwd = peewee.CharField()
	cookies = peewee.TextField()
	
	class Meta:
		table_name = "user"


class Conversation(BaseModel):
	username = peewee.CharField(primary_key=True)
	conversation_id = peewee.CharField()
	is_user = peewee.BooleanField()
	text_eng = peewee.TextField()
	text_zh = peewee.TextField()
	time = peewee.DateTimeField()
	text_id = peewee.CharField()
	
	class Meta:
		table_name = "conversation"


db.create_tables([User, Conversation])

if __name__ == "__main__":
	# res = User.insert({
	# 	User.username: "test",
	# 	User.passwd: "test",
	# }).execute()
	# print(res)
	a = User.select().execute()[0]
	print(a.email)
# for u in a:
# 	print(u.id, u.username, u.passwd, u.cookies)
