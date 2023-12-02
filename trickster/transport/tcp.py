import socket


def create_tcp_socket(server_side: bool, destination: tuple[str, int]):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if server_side:
        sock.connect(destination)
    else:
        sock.bind(destination)
        sock.listen()
    return sock
