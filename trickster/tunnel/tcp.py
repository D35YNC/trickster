import socket

from trickster.tunnel import Portal
from trickster.transport.tcp import create_tcp_socket

from trickster.transport import TricksterPayload


class TCPPortal(Portal):
    TCP_BUFFER_SIZE = 1024

    def __init__(self, *, bind: tuple[str, int] = None, endpoint: tuple[str, int] = None, is_enter: bool = False):
        super().__init__(endpoint, is_enter)
        self._connections = {}
        if bind:
            self._master_socket = create_tcp_socket(False, bind)
            self._sockets.append(self._master_socket)

    def process_data(self, sock: socket.socket) -> tuple[int | None, TricksterPayload | None]:
        if sock is self._master_socket:
            s, a = self._master_socket.accept()
            self.register(s)
            return None, None

        data = sock.recv(TCPPortal.TCP_BUFFER_SIZE)
        if not data:
            self.unregister(sock)
            return None, None

        id_ = None
        for k in self._connections:
            if self._connections[k] is sock:
                id_ = k
                break
        if not self._endpoint and self._is_enter:
            return id_, TricksterPayload.parse(data)
        return id_, TricksterPayload.create(sock.getpeername(), self._endpoint if self._endpoint else ('0.0.0.0', 0), data)

    def send_to(self, id: int, payload: TricksterPayload):
        if id not in self._connections:
            sock = create_tcp_socket(True, payload.dst)
            self.register(sock, id)

        if self._endpoint and not self._is_enter:
            self._connections[id].send(bytes(payload))
        else:
            self._connections[id].send(payload.data.rstrip(b"\x00\x11\x22"))

    def register(self, sock: socket.socket, id: int = None):
        if not id:
            id = sock.getpeername()[1]
        self._connections[id] = sock
        self._sockets.append(sock)

    def unregister(self, sock: socket.socket):
        if sock in self._sockets:
            self._sockets.remove(sock)
        for k in self._connections.keys():
            if self._connections[k] is sock:
                self._connections.pop(k)
                break
        sock.close()

