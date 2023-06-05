import base64
import hashlib
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


class BufferFromb64Decoder:
	def __init__(self):
		self.i = self.initI()
	
	def initI(self):
		s = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
		r = [None] * len(s)
		i = [None] * 123
		for a in range(len(s)):
			r[a] = s[a],
			i[ord(s[a])] = a
		i[ord("-")] = 62
		i[ord("_")] = 63
		return i
	
	def h(self, t: str):
		e = len(t)
		if e % 4 > 0:
			raise Exception("Invalid string. Length must be a multiple of 4")
		n = t.index("=") if "=" in t else -1
		if n == -1:
			n = e
		if n == e:
			r = 0
		else:
			r = 4 - n % 4
		return [n, r]
	
	def c(self, t, e, n):
		return int(3 * (e + n) / 4 - n)
	
	def deocde(self, t):
		r = self.h(t)
		s = r[0]
		a = r[1]
		u = np.zeros(self.c(t, s, a), dtype="uint8")
		f = 0
		if a > 0:
			l = s - 4
		else:
			l = s
		n = 0
		while n < l:
			e = self.i[ord(t[n])] << 18 | self.i[ord(t[n + 1])] << 12 | self.i[ord(t[n + 2])] << 6 | self.i[ord(t[n + 3])]
			u[f] = e >> 16 & 255
			f += 1
			u[f] = e >> 8 & 255
			f += 1
			u[f] = 255 & e
			f += 1
			n += 4
		if a == 2:
			e = self.i[ord(t[n])] << 2 | self.i[ord(t[n + 1])] >> 4
			u[f] = 255 & e
			f += 1
		if a == 1:
			e = self.i[ord(t[n])] << 10 | self.i[ord(t[n + 1])] << 4 | self.i[ord(t[n + 2])] >> 2
			u[f] = e >> 8 & 255
			f += 1
			u[f] = 255 & e
			f += 1
		return u


class YouDaoDecoder:
	def __init__(self):
		self.decode_key = "ydsecret://query/key/B*RGygVywfNBwpmBaZg*WT7SIOUP2T0C9WHMZN39j^DAdaZhAnxvGcCY6VYFwnHl"
		self.decode_iv = "ydsecret://query/iv/C@lZe2YzHtZ2CYgaXKSVfsb7Y4QWHjITPPZ0nQp87fBeJ!Iv6v^6fvi2WN@bYpJ4"
		self.b64Decoder = BufferFromb64Decoder()
	
	def getMD5(self, text: str):
		return hashlib.md5(text.encode("UTF-8"))
	
	def toUint8(self, text):
		dig = self.getMD5(text).digest()
		byte = bytearray(dig)
		return np.frombuffer(byte, dtype="uint8")
	
	def decode(self, text):
		key = self.toUint8(self.decode_key).tobytes()
		iv = self.toUint8(self.decode_iv).tobytes()
		text = self.b64Decoder.deocde(text)
		# print(text.tolist())
		cipher = AES.new(key, AES.MODE_CBC, iv)
		decrypt = cipher.decrypt(text.tobytes())
		# print(decrypt.decode())
		data = unpad(decrypt, AES.block_size).decode("utf-8")
		return data



if __name__ == "__main__":
	msg = "Z21kD9ZK1ke6ugku2ccWu-MeDWh3z252xRTQv-wZ6jd-f4VUaQOlThzHO02JcemZpYOzjRE7JK2Ol9PAth_lYMaENup_QEtlNJN4tjftwX-jtnM_K9V4WVSoMMLZwoBLlOHHOip1TuYCekJ1Ll4BLSGbHd_UXPNAulXK_u0qq5iIHmEqjZuiT4zLFxCw-yuNUZzO3Ykj4bZ-T7klCzHutBLgA4es6RJIvr8vHfUueKtIoWv_2kHfomR48ocEqMSrweme2nT89II-a76D7eUxdABSwcYIYRJdjS94_7xP_Vf8pPf9X0PoGm6zTXrieeyBqqa6MLxPJjMlOhigPP2vZClTGhS-sODgUbCelZdZu-zg-8Z7MwUqgVzCH5M41nnp8Ien0KZSRooD-xLTZGGOQJPWAmbPbyn93I_8RI5hMptTKOcjt_aF_H54TX-FoaUb96qRi1jRN5kQSabju77Mk26aGhpy9r6fwqVpA_hzaAQHc4BaJTn4YkiDhbT-5aEm1HlaOqJfUARd_Lc42u9MkrjFMO5UELIn3qsZzQzurf_Agi3m69c-frn7yEOnybCnALNKnDZpe6TqWAjr0zsT07GADGsvgIZPr4cxAZpQh-nwW9AkkWcUcylnseF-HclsbPU1Z5xIPdtW2i1agpOuCB63sbI0GWZbdEqui3iLrpAgBBSPIMBlWBE6JbViRoJcEzC5SmQJIkRYB0YQv2x-XW6jTcTa_yufDTGP1bQI0stgbrtWbRodCWb4L6uHxFNJldIqmjJJq50MxqimftY7LF1NxLnmCM1TJHWVDNBp_QeQ-uz_tU3t61Mgcy_khn-SLaXphL7Saw5K_gxipVZN-bRzbsAoU7Xl2IYe3orCHAaIMw5pzOwbsFPABK2t92o2UT3YrUI_pqPIkWBzG8c3XoGqIj3w5q48AIcrjvJGcvFKjsTT8pdvGIV282uCzT0uSVgr7RDK-YUJ0y4V0_YG1HwE1PO-0ekDqYYqRcUXVfZwqBlPzH282ISFONTYyYFDCTardtcygXI1RSpOnXPatnyyXZMmS7gOcEXepNIPmcgl2t3LocEjgvJbGB9fV-FnU_5sIEjSNZn9A7Z2qFzNRb2JrLaZD_jQEi7EPGXFMoQsjKZEvj40XJ_R_bgGuBhCV5gQd9kMlU7Iq6j7_s7FBJ1gKgC7BvIkTjeL5-y6Jx6rC8fJWiFw8rSpbPSqJm7-oIrzrNLyf-Q1k24g0XNBULAaT9L3vlgfTSLXWxvlNNWKOGC-iydGQlvBPOBuoMBXNmi8Sba7Ic6k3MkiR0GxMUOuXHw1UOjWMRi2TDcqHh2OAp2YqcXpsD4nqdJ4-_iRLHQ-H42Jx8gqa6AYwy1Y_Pckaj5S2SX1LZ9tbJShln6pz_717Ev2cNfkOtBqcV1hbBmSyggo4WPThSyLjWzFce6rhMfracBfo7EBfGcAQN6I1zahwhSOg02F3k6ykHILo3uxi8bIjAscpWR6_R5y9A=="
	ydDecoder = YouDaoDecoder()
	print(ydDecoder.decode(msg))
	a = base64.b64decode(msg)
	print(a)
	a = ydDecoder.b64Decoder.deocde(msg)
	print(a.tobytes())

