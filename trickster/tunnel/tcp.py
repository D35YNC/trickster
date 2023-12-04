import logging
import socket

from trickster.tunnel import Portal
from trickster.tunnel import PortalSide

from trickster.transport import TricksterPayload
from trickster.transport.tcp import create_tcp_socket


_LOGGER = logging.getLogger(__name__)


class TCPPortal(Portal):
    BUFFER_SIZE = 1024

    def __init__(self, *, bind: tuple[str, int] = None, interface: str = None, socket_timeout: int = None, **kwargs):
        super().__init__(**kwargs)
        self._connections = {}
        self._socket_timeout = socket_timeout
        if bind or (self._server and self._server_side):
            self._master_socket = create_tcp_socket(bind or self._server, True, interface, self._socket_timeout)
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

        if self._server_side:
            if self._server:
                # ITS SERVER TRANSPORT ENTRY (CHANNEL -> HERE -> EXIT)
                _LOGGER.debug("Processing payload as SERVER TRANSPORT ENTRY")
                if self._key:
                    payload = TricksterPayload.decrypt(payload, self._key)
                return id_, TricksterPayload.parse(payload)
            else:
                # ITS SERVER EXIT (TRANSPORT ENTRY -> HERE -> TARGET)
                _LOGGER.debug("Processing payload as SERVER EXIT")
                return id_, TricksterPayload.create(id_, sock.getpeername(), payload)
        else:
            if self._server:
                # ITS CLIENT TRANSPORT EXIT (CHANNEL -> HERE -> EXIT)
                _LOGGER.debug("Processing payload as CLIENT TRANSPORT EXIT")
                if self._key:
                    payload = TricksterPayload.decrypt(payload, self._key)
                return id_, TricksterPayload.parse(payload)
            else:
                # ITS CLIENT ENTRY (TRANSPORT EXIT -> HERE -> INPUT)
                _LOGGER.debug("Processing payload as CLIENT ENTRY")
                return id_, TricksterPayload.create(id_, self._endpoint, payload)

    def send_to(self, id: int, payload: TricksterPayload):
        _LOGGER.debug(f"Sending {len(payload.data)} bytes payload to {id}")
        if id not in self._connections:
            _LOGGER.debug(f"{id} not in sessions. Creating socket")
            sock = create_tcp_socket(payload.dst if self._server_side else self._server, timeout=self._socket_timeout)
            self.register(sock, id)

        if self._server_side:
            if self._server:
                # ITS SERVER TRANSPORT ENTRY ( CHANNEL -> HERE -> EXIT)
                _LOGGER.debug("Processing payload as SERVER TRANSPORT ENTRY")
                payload = bytes(payload)
                if self._key:
                    payload = TricksterPayload.encrypt(payload, self._key)
                self._connections[id].send(payload)
            else:
                # ITS SERVER EXIT (TRANSPORT ENTRY -> HERE -> TARGET)
                _LOGGER.debug("Processing payload as SERVER EXIT")
                self._connections[id].send(payload.data)
        else:
            if self._server:
                # ITS CLIENT TRANSPORT EXIT (ENTRY -> HERE -> CHANNEL)
                _LOGGER.debug("Processing payload as CLIENT TRANSPORT EXIT")
                payload = bytes(payload)
                if self._key:
                    payload = TricksterPayload.encrypt(payload, self._key)
                self._connections[id].send(payload)
            else:
                # ITS CLIENT ENTRY (TRANSPORT EXIT -> HERE -> INPUT)
                _LOGGER.debug("Processing payload as CLIENT ENTRY")
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

    def __contains__(self, item):
        return item in self._connections.keys() or item in self._connections.values()

    @staticmethod
    def side():
        return PortalSide.Both
