import base64
import logging

from trickster.tunnel import Tunnel
from trickster.tunnel import Portal
from trickster.tunnel import PortalSide
from trickster.tunnel.udp import UDPPortal
from trickster.tunnel.tcp import TCPPortal
from trickster.tunnel.icmp import ICMPPortal

from trickster.utils.args import create_server_parser
from trickster.utils.encryption import kdf

_LOGGER = logging.getLogger(__name__)


def server_main():
    enter = {cls.__name__[:-6].lower(): cls for cls in Portal.__subclasses__() if cls.side() == PortalSide.EntryOnly}
    transport = {cls.__name__[:-6].lower(): cls for cls in Portal.__subclasses__() if cls.side() == PortalSide.TransportOnly}
    universal = {cls.__name__[:-6].lower(): cls for cls in Portal.__subclasses__() if cls.side() == PortalSide.Both}
    parser = create_server_parser(list(enter.keys()), list(transport.keys()), list(universal.keys()))
    args = parser.parse_args()
    _LOGGER.debug(args)

    if args.addr:
        args.addr = args.addr.split(':')
        args.addr = (args.addr[0], int(args.addr[1]))

    if args.password:
        args.key = kdf(args.password)
    elif args.key:
        args.key = base64.b64decode(args.key)

    if args.key:
        _LOGGER.debug(f"Key: {args.key[:8]}...{args.key[-8:]}")

    exit_cls = enter.get(args.tunnel_exit) or universal.get(args.tunnel_exit)
    exit = exit_cls(key=args.key, socket_timeout=args.timeout, server_side=True)

    transport_cls = transport.get(args.tunnel_transport) or universal.get(args.tunnel_transport)
    transport = transport_cls(server=args.addr, socket_timeout=args.timeout, server_side=True)

    tun = Tunnel([exit], transport, True)
    tun.run()


if __name__ == '__main__':
    server_main()
