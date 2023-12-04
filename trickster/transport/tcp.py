import socket


def create_tcp_socket(destination: tuple[str, int], bind: bool = False, interface: str = None, timeout: int = None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if timeout:
        sock.settimeout(timeout)
    if bind:
        if interface:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface.encode("utf-8"))
        sock.bind(destination)
        sock.listen()
    else:
        sock.connect(destination)
    return sock
