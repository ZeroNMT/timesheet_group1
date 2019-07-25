import base64
import hashlib
from ..library.Crypto import Random
from ..library.Crypto.Cipher import AES


class AESCipher():

    def __init__(self):
        self.bs = 32
        self.key = hashlib.sha256("minhtham0zero@gmail.com".encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw)).decode("utf-8")

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    def decrypt(self, enc):
        enc = base64.b64decode(enc.encode("utf-8"))
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]