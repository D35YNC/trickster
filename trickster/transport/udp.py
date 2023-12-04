import socket


def create_udp_socket(addr: tuple[str, int] = None, bind_interface: str = None):
    if addr:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if bind_interface:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, bind_interface.encode("utf-8"))
        sock.bind(addr)
        return sock
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
