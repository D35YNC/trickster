import socket


def create_tcp_socket(destination: tuple[str, int], bind: bool = False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if bind:
        sock.bind(destination)
        sock.listen()
    else:
        sock.connect(destination)
    return sock
