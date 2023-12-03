import logging
import socket

from trickster.transport import TricksterPayload
from trickster.transport.tcp import create_tcp_socket

from trickster.tunnel import Portal

_LOGGER = logging.getLogger(__name__)


class TCPPortal(Portal):
    BUFFER_SIZE = 1024

    def __init__(self, *, bind: tuple[str, int] = None, endpoint: tuple[str, int] = None, is_enter: bool = False):
        super().__init__(endpoint, is_enter)
        self._connections = {}
        if bind:
            self._master_socket = create_tcp_socket(bind, True)
            self._sockets.append(self._master_socket)
        _LOGGER.debug(f"{self.__class__.__name__} initialized")#: {self}")

    def process_data(self, sock: socket.socket) -> tuple[int | None, TricksterPayload | None]:
        if sock is self._master_socket:
            s, a = self._master_socket.accept()
            _LOGGER.info(f"Accepted: {a}")
            self.register(s)
            return None, None

        payload = sock.recv(TCPPortal.BUFFER_SIZE)
        if not payload:
            self.unregister(sock)
            return None, None

        id_ = None
        for k in self._connections:
            if self._connections[k] is sock:
                id_ = k
                break

        _LOGGER.debug(f"Received {len(payload)} bytes payload from {id_}")

        if self._is_enter:
            if self._endpoint:
                # ITS CLIENT ENTER
                _LOGGER.debug("Processing payload as CLIENT ENTER")
                return id_, TricksterPayload.create(id_, self._endpoint, payload)
            else:
                # ITS SERVER ENTER
                _LOGGER.debug("Processing payload as SERVER ENTER")
                return id_, TricksterPayload.parse(payload)
        else:
            if self._endpoint:
                # ITS CLIENT EXIT
                _LOGGER.debug("Processing payload as CLIENT EXIT")
                return id_, TricksterPayload.parse(payload)
            else:
                # ITS SERVER EXIT
                _LOGGER.debug("Processing payload as SERVER EXIT")
                return id_, TricksterPayload.create(id_, sock.getpeername(), payload)

    def send_to(self, id: int, payload: TricksterPayload):
        _LOGGER.debug(f"Sending {len(payload.data)} payload to {id}")
        if id not in self._connections:
            _LOGGER.debug(f"{id} not in sessions. Creating socket")
            sock = create_tcp_socket(self._endpoint if self._endpoint else payload.dst)
            self.register(sock, id)

        if self._is_enter:
            if self._endpoint:
                # ITS CLIENT ENTER
                _LOGGER.debug("Processing payload as CLIENT ENTER")
                self._connections[id].send(payload.data)
            else:
                # ITS SERVER ENTER
                _LOGGER.debug("Processing payload as SERVER ENTER")
                self._connections[id].send(bytes(payload))
        else:
            if self._endpoint:
                # ITS CLIENT EXIT
                _LOGGER.debug("Processing payload as CLIENT EXIT")
                self._connections[id].send(bytes(payload))
            else:
                # ITS SERVER EXIT
                _LOGGER.debug("Processing payload as SERVER EXIT")
                self._connections[id].send(payload.data)

    def register(self, sock: socket.socket, id: int = None):
        if not id:
            id = sock.getpeername()[1]
        self._connections[id] = sock
        self._sockets.append(sock)
        _LOGGER.debug(f"{id} register")

    def unregister(self, sock: socket.socket):
        if sock in self._sockets:
            self._sockets.remove(sock)
        for k in self._connections.keys():
            if self._connections[k] is sock:
                _LOGGER.debug(f"{k} unregister")
                self._connections.pop(k)
                break
        sock.close()

