import socket

from trickster.tunnel import Portal
from trickster.transport.icmp import create_icmp_socket
from trickster.transport.icmp import ICMPType, ICMPPacket
from trickster.transport import TricksterPayload


class ICMPPortal(Portal):
    ICMP_BUFFER_SIZE = 65535

    def __init__(self, *, endpoint: tuple[str, int] = None, is_enter: bool = False):
        super().__init__(endpoint, is_enter)
        self._master_socket = create_icmp_socket()
        self._sockets.append(self._master_socket)
        self._connections = {}

    def process_data(self, sock: socket.socket) -> tuple[int | None, TricksterPayload | None]:
        packet, addr = sock.recvfrom(ICMPPortal.ICMP_BUFFER_SIZE)
        try:
            packet = ICMPPacket.parse(packet)
        except ValueError:
            print("Malformatted packet")
            return None, None

        if 16384 > packet.id:
            return None, None

        if packet.type == ICMPType.ECHO and packet.code == 0:
            # our packet, do nothing
            return None, None

        elif packet.type == ICMPType.ECHO_REQUEST and packet.code == 1:
            # control
            return packet.id, TricksterPayload.create(addr, ("", -1), bytes())
        else:
            self._connections[packet.id] = addr
            return packet.id, TricksterPayload.create(addr, packet.dst, packet.data)

        # if packet.type != ICMPType.ICMP_ECHO_REQUEST:
        #     return packet.id, packet.data

    def send_to(self, id: int, payload: TricksterPayload):
        if self._is_enter:
            packet = ICMPPacket.create(ICMPType.ECHO, 0, id, 0, payload.data, payload.src, payload.dst)
            self._master_socket.sendto(bytes(packet), (self._connections[packet.id][0], 0))
        else:
            packet = ICMPPacket.create(ICMPType.ECHO_REQUEST, 0, id, 0, payload.data, payload.src, payload.dst)
            self._master_socket.sendto(bytes(packet), (self._endpoint[0], 1))

