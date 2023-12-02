import abc
import select
import socket

from trickster.transport import TricksterPayload


class Portal(abc.ABC):
    def __init__(self):
        self._master_socket = None
        self._sockets = []

    @abc.abstractmethod
    def process_data(self, sock: socket.socket) -> tuple[int, TricksterPayload]:
        raise NotImplementedError()

    @abc.abstractmethod
    def send_to(self, id: int, data: TricksterPayload, exit: bool):
        raise NotImplementedError()

    def register(self, sock: socket.socket, id: int = None):
        pass

    def unregister(self, sock: socket.socket):
        pass

    @property
    @abc.abstractmethod
    def need_accept(self):
        raise NotImplementedError()

    @property
    def master_socket(self) -> socket.socket:
        return self._master_socket

    @property
    def sockets(self) -> list[socket.socket]:
        return self._sockets


class Tunnel:
    def __init__(self, enter_portal: Portal, exit_portal: Portal, target: tuple[str, int] = None):
        self.enter = enter_portal
        self.exit = exit_portal
        self.dst = target

    def run(self):
        while True:
            r, w, x = select.select(self.enter.sockets + self.exit.sockets, [], [])
            for sock in r:
                if sock is self.enter.master_socket:
                    if self.enter.need_accept:
                        s, a = self.enter.master_socket.accept()
                        self.enter.register(s)
                    else:
                        id, payload = self.enter.process_data(sock)
                        if 0 < id:
                            if self.dst:
                                payload.dst = self.dst
                            self.exit.send_to(id, payload, True)
                        else:
                            self.enter.unregister(sock)

                elif sock in self.enter.sockets:
                    id, payload = self.enter.process_data(sock)
                    if 0 < id:
                        if self.dst:
                            payload.dst = self.dst
                        self.exit.send_to(id, payload, True)
                    elif self.enter.need_accept:
                        self.enter.unregister(sock)

                elif sock is self.exit.master_socket:
                    if self.exit.need_accept:
                        s, a = self.exit.master_socket.accept()
                        self.exit.register(s)
                    else:
                        id, payload = self.exit.process_data(sock)
                        if 0 < id:
                            self.enter.send_to(id, payload, False)
                        elif self.exit.need_accept:
                            self.exit.unregister(sock)

                elif sock in self.exit.sockets:
                    id, payload = self.exit.process_data(sock)
                    if 0 < id:
                        self.enter.send_to(id, payload, False)
                    elif self.exit.need_accept:
                        self.exit.unregister(sock)

