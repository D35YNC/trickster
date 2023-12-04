import base64
import logging

from trickster.tunnel import Tunnel
from trickster.tunnel import Portal
from trickster.tunnel import PortalSide
from trickster.tunnel.udp import UDPPortal
from trickster.tunnel.tcp import TCPPortal
from trickster.tunnel.icmp import ICMPPortal

from trickster.utils.args import verify_tunnel_opts, create_client_parser
from trickster.utils.encryption import kdf

_LOGGER = logging.getLogger(__name__)


def client_main():
    enter = {cls.__name__[:-6].lower(): cls for cls in Portal.__subclasses__() if cls.side() == PortalSide.EntryOnly}
    transport = {cls.__name__[:-6].lower(): cls for cls in Portal.__subclasses__() if cls.side() == PortalSide.TransportOnly}
    universal = {cls.__name__[:-6].lower(): cls for cls in Portal.__subclasses__() if cls.side() == PortalSide.Both}

    parser = create_client_parser(list(enter.keys()), list(transport.keys()), list(universal.keys()))
    args = parser.parse_args()
    _LOGGER.debug(args)

    if args.password:
        args.key = kdf(args.password)
    elif args.key:
        args.key = base64.b64decode(args.key)

    if args.key:
        _LOGGER.debug(f"Key: {args.key[:8]}...{args.key[-8:]}")

    portals = []
    if args.local_tunnel:
        for lt in set(args.local_tunnel):
            options = lt.split(':')
            bind, port, host, hostport = "127.0.0.1", None, None, None
            match len(options):
                case 3:
                    port, host, hostport = options
                case 4:
                    bind, port, host, hostport = options
                case _:
                    parser.error(f"argument -L is malformed : '{lt}'")

            enter_cls = enter.get(args.tunnel_enter) or universal.get(args.tunnel_enter)
            if verify_tunnel_opts(bind, port, host, hostport):
                portals.append(enter_cls(bind=(bind, int(port)),
                                         endpoint=(host, int(hostport)),
                                         key=args.key,
                                         interface=args.interface,
                                         socket_timeout=args.timeout,
                                         server_side=False))
            else:
                parser.error(f"cant verify -L argument value : '{lt}'")

    if args.reverse_tunnel:
        _LOGGER.warning("Reverse tunnels not supported now")

    if args.dynamic_tunnel:
        _LOGGER.warning("Dynamic tunnels not supported now")

    if not portals:
        parser.error("No tunnels found")

    transport_cls = transport.get(args.tunnel_transport) or universal.get(args.tunnel_transport)
    transport = transport_cls(server=(args.server, args.port), socket_timeout=args.timeout, server_side=False)

    tun = Tunnel(portals, transport)
    tun.run()


if __name__ == "__main__":
    client_main()

