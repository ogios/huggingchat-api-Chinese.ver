from passlib.context import CryptContext
from jose import jwt, JWTError
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
import os
import base64


class UserManagement:
	def __init__(self):
		self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
		self.sessions = {}
		self.SECRET_KEY = "your_secret_key"
		self.ALGORITHM = "HS256"
		
		with open(os.path.dirname(os.path.abspath(__file__)) + "/public.pem", "r", encoding="utf-8") as f:
			self.public = f.read()
		with open(os.path.dirname(os.path.abspath(__file__)) + "/private.pem", "r", encoding="utf-8") as f:
			self.private = f.read()
		self.rsa_key = RSA.importKey(self.private)
		self.cipher = Cipher_pkcs1_v1_5.new(self.rsa_key)
	
	# def verifyPass(self, passwd: str, hash_passwd: str) -> bool:
	# 	return self.pwd_context.verify(passwd, hash_passwd)
	#
	# def getPassFromDB(self, email: str) -> str:
	# 	pass
	#
	# def checkUserFromDB(self, email: str) -> bool:
	# 	pass
	
	# def getPassHash(self, passwd: str) -> str:
	# 	return self.pwd_context.hash(passwd)
	
	def encodeToken(self, email: str):
		data = {"sub": email}
		return jwt.encode(data, self.SECRET_KEY, algorithm=self.ALGORITHM)
	
	def addUser(self, email: str, passwd: str) -> str:
		token = self.encodeToken(email)
		self.sessions[email] = {"token": token, "passwd": passwd}
		return token
	
	def checkUserExist(self, email: str, dec_passwd: str):
		if self.sessions.__contains__(email):
			if dec_passwd == self.sessions["email"]["passwd"]:
				return 1
		return 0
	
	# def activateUser(self, email, passwd) -> bool:
	# 	if self.checkUserFromDB(email):
	# 		hashed_pass = self.getPassFromDB(email)
	# 		if self.verifyPass(passwd, hashed_pass):
	# 			self.addUser(email, )
	# 			return True
	# 	return False
	
	def checkToken(self, token) -> bool:
		try:
			payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
			email: str = payload.get("sub")
			if not email or not self.sessions.__contains__(email):
				return False
			return True
		except JWTError:
			return False
	
	def decPass(self, enc_passwd):
		passwd = self.cipher.decrypt(base64.b64decode(enc_passwd), None)
		return passwd.decode("utf-8")
	
	def getTokenByEmail(self, email):
		if self.sessions.__contains__(email):
			return self.sessions[email]
		else:
			return None

if __name__ == "__main__":
	UM = UserManagement()
	# a = "IxfWc9eH0/21HU4yZ44RL3ZVp2keYD2+GUSCNH/HLj7e6ERkCWFOJl2otoU/xWLQgMWHdRuXzQSJR4zENtpHNh0vZBUhvR0bvsnvuouG+ZLCjVAl+bneUxfikgf8ZjYnH4f8hUDQH8hE/t++MqEgcKcPNZATjX+QlNmAajSUjr0="
	# print(UM.decPass(a))
	data = {
		"email": "156452@fasf.cndsa",
		"passwd": "7984563",
	}
	token = UM.addUser(data["email"], data["passwd"])
	print(UM.checkToken("token"))
	
	
	
	
	
	
	
	
	
	
	