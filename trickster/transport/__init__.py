import abc
import dataclasses
import socket
import struct


@dataclasses.dataclass
class Header(abc.ABC):
    def __bytes__(self):
        raise NotImplementedError()

    @staticmethod
    @abc.abstractmethod
    def get_struct_format():
        raise NotImplementedError()


@dataclasses.dataclass
class TricksterPayload:
    src: tuple[str, int]
    dst: tuple[str, int]
    data: bytes

    @classmethod
    def create(cls, src: tuple[str, int], dst: tuple[str, int], data: bytes):
        return cls(src, dst, data)

    @classmethod
    def parse(cls, data: bytes):
        fmt = TricksterPayload.get_struct_format()
        if 0 < (data_len := len(data) - 12):
            fmt += f"{data_len}s"
        src, src_port, dst, dst_port, data = struct.unpack(fmt, data)
        return cls((socket.inet_ntoa(src), src_port), (socket.inet_ntoa(dst), dst_port), data)

    @staticmethod
    def encrypt(packet: bytes, key: bytes) -> bytes:
        raise NotImplementedError()

    @staticmethod
    def decrypt(packet: bytes, key: bytes) -> bytes:
        raise NotImplementedError()

    @abc.abstractmethod
    def __bytes__(self) -> bytes:
        fmt = TricksterPayload.get_struct_format()
        args = [socket.inet_aton(self.src[0]), self.src[1], socket.inet_aton(self.dst[0]), self.dst[1]]
        if 0 < len(self.data):
            # TODO: Rewrite pad-unpad
            self.data += b"\x00\x11\x22" * (len(self.data) % 2)  # Add padding
            fmt += f"{len(self.data)}s"
            args.append(self.data)
        return struct.pack(fmt, *args)

    @staticmethod
    def get_struct_format() -> str:
        return "!4sH4sH"


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

    def __getattr__(self, item):
        if hasattr(self.header, item):
            return getattr(self.header, item)
        elif hasattr(self.payload, item):
            return getattr(self.payload, item)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

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

