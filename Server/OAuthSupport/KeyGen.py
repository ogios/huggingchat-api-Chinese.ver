import os
from Crypto import Random
from Crypto.PublicKey import RSA

random_generator = Random.new().read
rsa = RSA.generate(1024, random_generator)

# 生成私钥
private_key = rsa.exportKey()
with open(os.path.dirname(os.path.abspath(__file__)) + '/private.pem', 'w') as f:
	f.write(private_key.decode('utf-8'))

# 生成公钥
public_key = rsa.publickey().exportKey()
with open(os.path.dirname(os.path.abspath(__file__)) + '/public.pem', 'w') as f:
	f.write(public_key.decode('utf-8'))
