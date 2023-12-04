import base64
import logging

from trickster.tunnel import Tunnel
from trickster.tunnel import Portal
from trickster.tunnel import PortalSide
from trickster.tunnel.udp import UDPPortal
from trickster.tunnel.tcp import TCPPortal
from trickster.tunnel.icmp import ICMPPortal

from trickster.utils.args import verify_tunnel_opts, create_tunnel_parser
from trickster.utils.encryption import kdf

_LOGGER = logging.getLogger(__name__)


def tunnel_main():
    enter = {cls.__name__[:-6].lower(): cls for cls in Portal.__subclasses__() if cls.side() == PortalSide.EntryOnly}
    transport = {cls.__name__[:-6].lower(): cls for cls in Portal.__subclasses__() if cls.side() == PortalSide.TransportOnly}
    universal = {cls.__name__[:-6].lower(): cls for cls in Portal.__subclasses__() if cls.side() == PortalSide.Both}

    parser = create_tunnel_parser(list(enter.keys()), list(transport.keys()), list(universal.keys()))
    args = parser.parse_args()
    _LOGGER.debug(args)

    if args.password:
        args.key = kdf(args.password)
    elif args.key:
        args.key = base64.b64decode(args.key)

    if args.key:
        _LOGGER.debug(f"Key: {args.key[:8]}...{args.key[-8:]}")

    if args.remote:
        dst, dst_port = args.remote.split(':')
        dst_port = int(dst_port)
        tun = Tunnel(enter_portal, exit_portal, (dst, dst_port))
    else:
        tun = Tunnel(enter_portal, exit_portal)
    tun.run()


if __name__ == "__main__":
    tunnel_main()

