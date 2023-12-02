import socket

from trickster.tunnel import Portal
from trickster.transport.icmp import create_icmp_socket
from trickster.transport.icmp import ICMPType, ICMPPacket
from trickster.transport import TricksterPayload


class ICMPPortal(Portal):
    ICMP_BUFFER_SIZE = 65535

    def __init__(self, *, proxy: tuple[str, int] = None):
        super().__init__()
        self._master_socket = create_icmp_socket()
        self._sockets.append(self._master_socket)
        self.proxy = proxy
        self.s = {}

    def process_data(self, sock: socket.socket) -> tuple[int, TricksterPayload]:
        packet, addr = sock.recvfrom(ICMPPortal.ICMP_BUFFER_SIZE)
        try:
            packet = ICMPPacket.parse(packet)
        except ValueError:
            print("Malformatted packet")
            return -1, TricksterPayload.create(addr, (str(), -1), bytes())

        if 16384 > packet.id:
            return -1, TricksterPayload.create(addr, (str(), -1), bytes())

        if packet.type == ICMPType.ECHO and packet.code == 0:
            # our packet, do nothing
            pass
            print('im zalooped here')
            return -1, TricksterPayload.create(addr, (str(), -1), bytes())

        elif packet.type == ICMPType.ECHO_REQUEST and packet.code == 1:
            # control
            return packet.id, TricksterPayload.create(addr, ("", -1), bytes())
        else:
            self.s[packet.id] = addr
            return packet.id, TricksterPayload.create(addr, packet.dst, packet.data)

        # if packet.type != ICMPType.ICMP_ECHO_REQUEST:
        #     return packet.id, packet.data

    def send_to(self, id: int, payload: TricksterPayload, exit):
        if id < 0:
            return

        if exit:
            packet = ICMPPacket.create(ICMPType.ECHO_REQUEST, 0, id, 0, payload.data, payload.src, payload.dst)
            self._master_socket.sendto(bytes(packet), (self.proxy[0], 1))
        else:
            packet = ICMPPacket.create(ICMPType.ECHO, 0, id, 0, payload.data, payload.src, payload.dst)
            self._master_socket.sendto(bytes(packet), (self.s[packet.id][0], 0))

    @property
    def need_accept(self):
        return False
