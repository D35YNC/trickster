import argparse

from trickster.tunnel import __version__


def verify_tunnel_opts(bind: str, port: int, host: str, hostport: int):
    try:
        return all(
            [isinstance(bind, str), bind.count('.') == 3] +
            [0x00 < int(port) < 0xFFFF] +
            [isinstance(host, str)] +
            [0x00 < int(hostport) < 0xFFFF]
        )
    except ValueError:
        return False


def create_client_parser(enter_portals: list[str], transport_portals: list[str], universal_portals: list[str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("trickster-client",
                                     description="trickster.client description TODO")
    parser.add_argument("-s", "--server", type=str, metavar="IP",
                        help="remote server hostname or ip")
    parser.add_argument("-p", "--port", type=int,
                        help="remote server port")
    parser.add_argument("-i", "--interface", type=str,
                        help="interface to bind, used with -L")
    parser.add_argument("-e", "--tunnel-enter", type=str, choices=enter_portals + universal_portals,
                        help="protocol for tunnel entry")
    parser.add_argument("-t", "--tunnel-transport", type=str, choices=transport_portals + universal_portals,
                        help="protocol for tunneling")
    kdf_group = parser.add_mutually_exclusive_group()
    kdf_group.add_argument("-P", "--password", type=str,
                           help="password for tunnel encryption")
    kdf_group.add_argument("-k", "--key", type=str,
                           help="base64 encoded key")
    parser.add_argument("-L", dest="local_tunnel", type=str, action="append", metavar="[BIND_ADDRESS:]PORT:HOST:HOSTPORT",
                        help="local tunnel options")
    parser.add_argument("-R", dest="reverse_tunnel", type=str, action="append", metavar="[BIND_ADDRESS:]PORT:HOST:HOSTPORT",
                        help="reverse tunnel options")
    parser.add_argument("-D", dest="dynamic_tunnel", type=str, action="append", metavar="[BIND_ADDRESS:]PORT",
                        help="bind tunnel options")
    parser.add_argument("-T", "--socket-timeout", type=int, metavar="TIMEOUT",
                        help="socket timeout in seconds")
    parser.add_argument("-c", "--config", type=argparse.FileType("r+", encoding="utf-8"),
                        help="config")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s v{__version__}")
    return parser


def create_server_parser(enter_portals: list[str], transport_portals: list[str], universal_portals: list[str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("trickster-server",
                                     description="trickster.server description TODO")
    parser.add_argument("-A", "--addr", type=str, metavar="IP:PORT",
                        help="bind address")
    parser.add_argument("-i", "--interface", type=str,
                        help="interface to bind")
    parser.add_argument("-e", "--tunnel-exit", type=str, choices=enter_portals + universal_portals,
                        help="protocol for tunnel exit, must match client setting")
    parser.add_argument("-t", "--tunnel-transport", type=str, choices=transport_portals + universal_portals,
                        help="protocol for tunneling, must match client setting")
    kdf_group = parser.add_mutually_exclusive_group()
    kdf_group.add_argument("-P", "--password", type=str,
                           help="password for tunnel encryption")
    kdf_group.add_argument("-k", "--key", type=str,
                           help="base64 encoded key")
    parser.add_argument("-T", "--socket-timeout", type=int, metavar="TIMEOUT",
                        help="socket timeout in seconds")
    parser.add_argument("-c", "--config", type=argparse.FileType("r+", encoding="utf-8"),
                        help="config")
    return parser
