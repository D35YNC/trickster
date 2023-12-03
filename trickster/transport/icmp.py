import socket
import struct
import enum
from dataclasses import dataclass

from trickster.transport import Header, TricksterPayload, Packet


def create_icmp_socket(*args):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except socket.error:
        raise
    else:
        return sock


class ICMPType(enum.Enum):
    ECHO = 0
    ECHO_REQUEST = 8


@dataclass
class ICMPHeader(Header):
    type: ICMPType
    code: int
    id: int
    sequence: int
    checksum: int = 0

    @staticmethod
    def get_struct_format():
        return "!BBHHH"

    def __bytes__(self):
        args = [self.type.value, self.code, self.checksum, self.id, self.sequence]
        return struct.pack(ICMPHeader.get_struct_format(), *args)


@dataclass
class ICMPPacket(Packet):
    @classmethod
    def create(cls, type: ICMPType, code: int, id: int, sequence: int, data: bytes, src, dst: tuple[str, int]):
        return cls(
            ICMPHeader(type, code, id, sequence),
            TricksterPayload(src, dst, data)
        )

    @classmethod
    def parse(cls, packet: bytes):
        # ip_packet_format = "BBHHHBBH4s4s"
        icmp_packet_format = ICMPHeader.get_struct_format() + TricksterPayload.get_struct_format().lstrip('!')
        ip_packet, icmp_packet = packet[:20], packet[20:]  # split ip header
        # ip_packet = struct.unpack(ip_packet_format, ip_packet)
        # src_ip = ip_packet[8]
        icmp_packet_size = struct.calcsize(icmp_packet_format)
        data_size = len(icmp_packet) - icmp_packet_size

        data = b""
        if 0 < data_size:
            icmp_data_str = f"{data_size}s"
            data = struct.unpack(icmp_data_str, icmp_packet[icmp_packet_size:])[0]
        try:
            type, code, checksum, id, sequence, src, src_port, dst, dst_port = struct.unpack(icmp_packet_format, icmp_packet[:icmp_packet_size])
        except struct.error:
            return cls(ICMPHeader(0, 0, 0, 0), TricksterPayload(('', 0), ('', 0), bytes()))
        else:
            return cls(
                ICMPHeader(type, code, id, sequence, checksum),
                TricksterPayload((socket.inet_ntoa(src), src_port), (socket.inet_ntoa(dst), dst_port), data)
            )

