import logging
import socket

from trickster.tunnel import Portal
from trickster.tunnel import PortalSide

from trickster.transport.icmp import create_icmp_socket
from trickster.transport.icmp import ICMPType
from trickster.transport.icmp import ICMPPacket

from trickster.transport import TricksterPayload

_LOGGER = logging.getLogger(__name__)


class ICMPPortal(Portal):
    BUFFER_SIZE = 65535

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._master_socket = create_icmp_socket()
        self._sockets.append(self._master_socket)
        self._connections = {}
        _LOGGER.debug(f"{self.__class__.__name__} initialized")#: {self}")

    def process_data(self, sock: socket.socket) -> tuple[int | None, TricksterPayload | None]:
        data, addr = sock.recvfrom(ICMPPortal.BUFFER_SIZE)
        try:
            packet = ICMPPacket.parse(data)
        except ValueError:
            _LOGGER.error(f"Malformatted packet received: {data}")
            return None, None

        if 16384 > packet.header.id:
            return None, None

        _LOGGER.debug(f"Received {len(packet.payload.data)} bytes payload from {packet.header.id}")

        if packet.header.type == ICMPType.ECHO and packet.header.code == 0:
            # our packet, do nothing
            return None, None

        elif packet.header.type == ICMPType.ECHO_REQUEST and packet.header.code == 1:
            # control
            _LOGGER.debug(f"{packet.header.id} session end ?")  # IDK
            self._connections.pop(packet.header.id)
            return packet.header.id, None
        else:
            self._connections[packet.header.id] = addr
            return packet.header.id, TricksterPayload.create(packet.header.id, packet.payload.dst, packet.payload.data)

    def send_to(self, id: int, payload: TricksterPayload):
        if self._server_side:
            # ITS SERVER TRANSPORT ENTRY (EXIT -> HERE -> CHANNEL)
            _LOGGER.debug("Processing payload as SERVER TRANSPORT ENTRY")
            packet = ICMPPacket.create(ICMPType.ECHO, 0, id, 0, payload.dst, payload.data)
            dst = (self._connections[packet.header.id][0], 0)
        else:
            # ITS CLIENT TRANSPORT EXIT (ENTRY -> HERE -> CHANNEL)
            _LOGGER.debug("Processing payload as CLIENT TRANSPORT EXIT")
            packet = ICMPPacket.create(ICMPType.ECHO_REQUEST, 0, id, 0, payload.dst, payload.data)
            dst = (self._server[0], 1)

        _LOGGER.debug(f"Sending {len(packet.payload.data)} bytes payload to {packet.header.id}")
        self._master_socket.sendto(bytes(packet), dst)

    def __contains__(self, item):
        return item in self._connections.keys()

    @staticmethod
    def side():
        return PortalSide.TransportOnly
