import abc
import enum
import logging
import select
import socket

from trickster.transport import TricksterPayload

_LOGGER = logging.getLogger(__name__)


class PortalSide(enum.Enum):
    TransportOnly = 0
    EntryOnly = 1
    Both = 10


class Portal(abc.ABC):
    def __init__(self, **kwargs):
        self._key = kwargs.get("key")
        self._endpoint = kwargs.get("endpoint")
        self._server = kwargs.get("server")
        self._server_side = kwargs.get("server_side")
        self._master_socket = None
        self._sockets = []

    @abc.abstractmethod
    def process_data(self, sock: socket.socket) -> tuple[int, TricksterPayload]:
        raise NotImplementedError()

    @abc.abstractmethod
    def send_to(self, id: int, payload: TricksterPayload):
        raise NotImplementedError()

    @property
    def sockets(self) -> list[socket.socket]:
        return self._sockets

    @staticmethod
    @abc.abstractmethod
    def side():
        raise NotImplementedError()

    @abc.abstractmethod
    def __contains__(self, item):
        raise NotImplementedError()


class Tunnel:
    def __init__(self, enter_portal: list[Portal] | tuple[Portal], transport_portal: Portal, server_side: bool = False):
        self.enter = enter_portal
        self.transport = transport_portal
        self._server_side = server_side
        _LOGGER.debug(f"{self.__class__.__name__} initialized")

    def run(self):
        sockets = []
        while True:
            sockets.clear()
            for enter in self.enter:
                sockets.extend(enter.sockets)
            r, w, x = select.select(sockets + self.transport.sockets, [], [])
            for sock in r:
                for enter in self.enter:
                    if sock in enter.sockets:
                        id_, payload = enter.process_data(sock)
                        _LOGGER.debug(f"From enter {enter}: {id_}, {payload}")
                        if id_:
                            self.transport.send_to(id_, payload)
                        break
                else:
                    if sock in self.transport.sockets:
                        id_, payload = self.transport.process_data(sock)
                        _LOGGER.debug(f"From transport: {id_}, {payload}")
                        if id_:
                            if self._server_side:
                                self.enter[0].send_to(id_, payload)
                            else:
                                for enter in self.enter:
                                    if id_ in enter:
                                        enter.send_to(id_, payload)
