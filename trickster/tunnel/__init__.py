import abc
import select
import socket

from trickster.transport import TricksterPayload

from trickster.utils.logging import create_full_logger
_LOGGER = create_full_logger(__name__)


class Portal(abc.ABC):
    def __init__(self, endpoint: tuple[str, int] = None, is_enter: bool = False):
        self._endpoint = endpoint
        self._is_enter = is_enter
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

    @property
    def endpoint(self) -> tuple[str, int]:
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        if value is None:
            self._endpoint = value
            return
        elif isinstance(value, tuple) and len(value) == 2:
            if isinstance(value[0], str) and isinstance(value[1], int):
                self._endpoint = value
                return
        raise ValueError(f"Cant assign {value} to tuple[str, int]")


class Tunnel:
    def __init__(self, enter_portal: Portal, exit_portal: Portal, target: tuple[str, int] = None):
        self.enter = enter_portal
        self.exit = exit_portal
        self.enter.endpoint = target
        _LOGGER.debug(f"{self.__class__.__name__} initialized")

    def run(self):
        while True:
            r, w, x = select.select(self.enter.sockets + self.exit.sockets, [], [])
            for sock in r:
                if sock in self.enter.sockets:
                    id_, payload = self.enter.process_data(sock)
                    _LOGGER.debug(f"From enter: {id_}, {payload}")
                    if id_:
                        self.exit.send_to(id_, payload)

                elif sock in self.exit.sockets:
                    id_, payload = self.exit.process_data(sock)
                    _LOGGER.debug(f"From exit: {id_}, {payload}")
                    if id_:
                        self.enter.send_to(id_, payload)
