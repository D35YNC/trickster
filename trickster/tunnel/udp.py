import logging
import socket

from trickster.tunnel import Portal
from trickster.tunnel import PortalSide

from trickster.transport import TricksterPayload
from trickster.transport.udp import create_udp_socket


_LOGGER = logging.getLogger(__name__)


class UDPPortal(Portal):
    BUFFER_SIZE = 65535

    def __init__(self, *, bind: tuple[str, int] = None, interface: str = None, **kwargs):
        super().__init__(**kwargs)
        self._master_socket = create_udp_socket(bind, interface)
        self._sockets.append(self._master_socket)
        self._connections = {}
        _LOGGER.debug(f"{self.__class__.__name__} initialized")#: {self}")

    def process_data(self, sock: socket.socket) -> tuple[int | None, TricksterPayload | None]:
        payload, addr = sock.recvfrom(UDPPortal.BUFFER_SIZE)
        id_ = addr[1]
        # CAnt use this identification method with udp exits
        # hmmmmmm
        _LOGGER.debug(f"Received {len(payload)} bytes payload from {id_}")

        if id_ not in self._connections:
            self._connections[id_] = addr

        if self._server_side:
            if self._server:
                # ITS SERVER TRANSPORT ENTRY ( CHANNEL -> HERE -> EXIT)
                _LOGGER.debug("Processing payload as SERVER TRANSPORT ENTRY")
                if self._key:
                    payload = TricksterPayload.decrypt(payload, self._key)
                payload = TricksterPayload.parse(payload)
                # self._connections.pop(id_)
                # if payload.session_id not in self._connections:
                #     self._connections[payload.session_id] = addr
                return payload.session_id, payload
            else:
                # ITS SERVER EXIT ( CHANNEL -> TRANSPORT ENTRY -> HERE)
                _LOGGER.debug("Processing payload as SERVER EXIT")
                return id_, TricksterPayload.create(id_, self._endpoint, payload)
                # payload = TricksterPayload.parse(payload)
                # self._connections.pop(id_)
                # if payload.session_id not in self._connections:
                #     self._connections[payload.session_id] = addr
                # return payload.session_id, payload
        else:
            if self._server:
                # ITS CLIENT TRANSPORT EXIT (ENTRY -> HERE -> CHANNEL)
                _LOGGER.debug("Processing payload as CLIENT TRANSPORT EXIT")
                if self._key:
                    payload = TricksterPayload.decrypt(payload, self._key)
                payload = TricksterPayload.parse(payload)
                return payload.session_id, payload
            else:
                # ITS CLIENT ENTRY (-> HERE -> TRANSPORT EXIT)
                _LOGGER.debug("Processing payload as CLIENT ENTRY")
                return id_, TricksterPayload.create(id_, self._endpoint, payload)

    def send_to(self, id_: int, payload: TricksterPayload):
        _LOGGER.debug(f"Sending {len(payload.data)} bytes payload to {id_}")

        if self._server_side:
            if self._server:
                # ITS SERVER TRANSPORT ENTRY ( CHANNEL -> HERE -> EXIT)
                _LOGGER.debug("Processing payload as SERVER TRANSPORT ENTRY")
                payload = bytes(payload)
                if self._key:
                    payload = TricksterPayload.encrypt(payload, self._key)
                self._master_socket.sendto(payload, self._connections[id_])
            else:
                # ITS SERVER EXIT (TRANSPORT ENTRY -> HERE -> TARGET)
                _LOGGER.debug("Processing payload as SERVER EXIT")
                if id_ not in self._connections:
                    self._connections[id_] = payload.dst
                self._master_socket.sendto(payload.data, self._connections[id_])
        else:
            if self._server:
                # ITS CLIENT TRANSPORT EXIT (ENTRY -> HERE -> CHANNEL)
                _LOGGER.debug("Processing payload as CLIENT TRANSPORT EXIT")
                payload = bytes(payload)
                if self._key:
                    payload = TricksterPayload.encrypt(payload, self._key)
                self._master_socket.sendto(payload, self._endpoint)
            else:
                # ITS CLIENT ENTRY (TRANSPORT EXIT -> HERE -> INPUT)
                _LOGGER.debug("Processing payload as CLIENT ENTRY")
                self._master_socket.sendto(payload.data, self._connections[id_])

    def __contains__(self, item):
        return item in self._connections.keys()

    @staticmethod
    def side():
        return PortalSide.Both
