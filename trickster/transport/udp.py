import socket


def create_udp_socket(addr: tuple[str, int] = None):
    if addr:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(addr)
        return sock
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
