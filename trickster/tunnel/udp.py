import logging
import socket

from trickster.transport import TricksterPayload
from trickster.transport.udp import create_udp_socket

from trickster.tunnel import Portal

_LOGGER = logging.getLogger(__name__)


class UDPPortal(Portal):
    BUFFER_SIZE = 65535

    def __init__(self, *, bind: tuple[str, int] = None, endpoint: tuple[str, int] = None, is_enter: bool = False):
        super().__init__(endpoint, is_enter)
        self._master_socket = create_udp_socket(bind)
        self._sockets.append(self._master_socket)
        self._connections = {}
        _LOGGER.debug(f"{self.__class__.__name__} initialized")#: {self}")

    def process_data(self, sock: socket.socket) -> tuple[int | None, TricksterPayload | None]:
        payload, addr = sock.recvfrom(UDPPortal.BUFFER_SIZE)
        id_ = addr[1]

        _LOGGER.debug(f"Received {len(payload)} bytes payload from {id_}")

        if id_ not in self._connections:
            self._connections[id_] = addr

        if self._is_enter:
            if self._endpoint:
                # ITS TUNNEL CLIENT ENTER
                _LOGGER.debug("Processing payload as CLIENT ENTER")
                return id_, TricksterPayload.create(id_, self._endpoint, payload)
            else:
                # ITS TUNEL SERVER ENTER
                _LOGGER.debug("Processing payload as SERVER ENTER")
                payload = TricksterPayload.parse(payload)
                self._connections.pop(id_)
                if payload.session_id not in self._connections:
                    self._connections[payload.session_id] = addr
                return payload.session_id, payload
                # return id_, TricksterPayload.parse(payload)
        else:
            if self._endpoint:
                # ITS CLIENT EXIT
                _LOGGER.debug("Processing payload as CLIENT EXIT")
                payload = TricksterPayload.parse(payload)
                return payload.session_id, payload
            else:
                # ITS SERVER EXIT
                _LOGGER.debug("Processing payload as SERVER EXIT")
                payload = TricksterPayload.parse(payload)
                self._connections.pop(id_)
                if payload.session_id not in self._connections:
                    self._connections[payload.session_id] = addr
                return payload.session_id, payload

    def send_to(self, id: int, payload: TricksterPayload):
        _LOGGER.debug(f"Sending {len(payload.data)} bytes payload to {id}")

        if self._is_enter:
            if self._endpoint:
                # ITS CLIENT ENTER
                _LOGGER.debug("Processing payload as CLIENT ENTER")
                self._master_socket.sendto(payload.data, self._connections[id])
            else:
                # ITS SERVER ENTER
                _LOGGER.debug("Processing payload as SERVER ENTER")
                self._master_socket.sendto(bytes(payload), self._connections[id])
        else:
            if self._endpoint:
                # ITS CLIENT EXIT
                _LOGGER.debug("Processing payload as CLIENT EXIT")
                self._master_socket.sendto(bytes(payload), self._endpoint)
            else:
                # ITS SERVER EXIT
                _LOGGER.debug("Processing payload as SERVER EXIT")
                self._master_socket.sendto(payload.data, self._connections[id])
