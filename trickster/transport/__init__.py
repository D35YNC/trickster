import abc
import dataclasses
import socket
import struct

from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA512
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES


@dataclasses.dataclass
class Header(abc.ABC):
    def __bytes__(self):
        raise NotImplementedError()

    @staticmethod
    @abc.abstractmethod
    def get_struct_format():
        raise NotImplementedError()


# TODO: Rewrite pad-unpad
@dataclasses.dataclass
class TricksterPayload:
    session_id: int
    dst: tuple[str, int]
    data: bytes

    @classmethod
    def create(cls, session_id: int, dst: tuple[str, int], data: bytes):
        return cls(session_id, dst, data.rstrip(b"\x00\x11\x22"))
    # def create(cls, src: tuple[str, int], dst: tuple[str, int], data: bytes):
        # return cls(src, dst, data)

    @classmethod
    def parse(cls, data: bytes):
        fmt = TricksterPayload.get_struct_format()
        if 0 < (data_len := len(data) - struct.calcsize(fmt)):
            fmt += f"{data_len}s"
        session_id, dst, dst_port, data = struct.unpack(fmt, data)
        return cls(session_id, (socket.inet_ntoa(dst), dst_port), data.rstrip(b"\x00\x11\x22"))

    @staticmethod
    def encrypt(packet: bytes, password: str) -> bytes:
        print('Encrypt')
        salt = get_random_bytes(16)
        key = PBKDF2(password, salt, 32, count=100000, hmac_hash_module=SHA512)
        aes = AES.new(key, AES.MODE_GCM)
        cipher, tag = aes.encrypt_and_digest(packet)
        return salt + aes.nonce + cipher + tag

    @staticmethod
    def decrypt(packet: bytes, password: str) -> bytes:
        salt, nonce, cipher, tag = packet[:16], packet[16:32], packet[32:-16], packet[-16:]
        key = PBKDF2(password, salt, count=100000, hmac_hash_module=SHA512)
        aes = AES.new(key, AES.MODE_GCM, nonce)
        return aes.decrypt_and_verify(cipher, tag)

    @abc.abstractmethod
    def __bytes__(self) -> bytes:
        fmt = TricksterPayload.get_struct_format()
        args = [self.session_id, socket.inet_aton(self.dst[0]), self.dst[1]]
        if 0 < len(self.data):
            self.data += b"\x00\x11\x22" * (len(self.data) % 2)  # Add padding
            fmt += f"{len(self.data)}s"
            args.append(self.data)
        return struct.pack(fmt, *args)

    @staticmethod
    def get_struct_format() -> str:
        return "!H4sH"


@dataclasses.dataclass
class Packet(abc.ABC):
    header: Header
    payload: TricksterPayload

    @classmethod
    @abc.abstractmethod
    def create(cls, *args):
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def parse(cls, packet: bytes):
        raise NotImplementedError()

    def __bytes__(self):
        self.header.checksum = Packet.checksum(bytes(self.header) + bytes(self.payload))
        return bytes(self.header) + bytes(self.payload)

    @staticmethod
    def checksum(packet: bytes) -> int:
        chksum = 0
        count_to = (len(packet) / 2) * 2
        count = 0
        while count < count_to:
            this_val = packet[count + 1] * 256 + packet[count]
            chksum = chksum + this_val
            chksum = chksum & 0xffffffff
            count = count + 2
        if count_to < len(packet):
            chksum = chksum + packet[len(packet) - 1]
            chksum = chksum & 0xffffffff
        chksum = (chksum >> 16) + (chksum & 0xffff)
        chksum = chksum + (chksum >> 16)
        answer = ~chksum
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer

