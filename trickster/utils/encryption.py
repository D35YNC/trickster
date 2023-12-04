from Crypto.Hash import SHA512, SHA256
from Crypto.Protocol.KDF import PBKDF2


def kdf(password: str):
    return PBKDF2(password, SHA256.new(password.encode()).digest(), 32, count=1000000000, hmac_hash_module=SHA512)
