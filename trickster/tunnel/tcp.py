import socket

from trickster.tunnel import Portal
from trickster.transport.tcp import create_tcp_socket

from trickster.transport import TricksterPayload


class TCPPortal(Portal):
    TCP_BUFFER_SIZE = 1024

    def __init__(self, *, bind: tuple[str, int] = None):
        super().__init__()
        self._connections = {}
        if bind:
            self._master_socket = create_tcp_socket(False, bind)
            self._sockets.append(self._master_socket)

    def process_data(self, sock: socket.socket) -> tuple[int, TricksterPayload]:
        data = sock.recv(TCPPortal.TCP_BUFFER_SIZE)
        id_ = -1
        if not data:
            # addr = sock.getpeername()
            # self.unregister(sock, addr)
            return id_, TricksterPayload.create(("", 0), ("", 0), data)

        for k in self._connections:
            if self._connections[k] is sock:
                id_ = k
                break
        return id_, TricksterPayload.create(sock.getpeername(), ("0.0.0.0", 0), data) # if self._master_socket else TricksterPayload.parse(data)

    def send_to(self, id: int, payload: TricksterPayload, exit: bool):
        if id in self._connections:
            self._connections[id].send(payload.data)
        else:
            sock = create_tcp_socket(True, payload.dst)
            self.register(sock, id)
            sock.send(payload.data)

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

    @property
    def need_accept(self):
        return True
