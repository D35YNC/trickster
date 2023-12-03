import argparse

from trickster.utils.portal_factory import PortalFactory
from trickster.tunnel import Tunnel


def tunnel_main():
    parser = argparse.ArgumentParser(description="trickster.tunnel is sussy amongus sus impostor tunnel")

    parser.add_argument("enter", type=str,
                        help="tunnel enter point url-like string: tcp://127.0.0.1:1080")
    parser.add_argument("exit", type=str,
                        help="tunnel enter point url-like string: icmp://TARGET")
    parser.add_argument("-t", "--remote", type=str,
                        help="tunnel destination point: ip:port")
    args = parser.parse_args()

    enter_portal = PortalFactory.from_url(args.enter + "/enter")
    exit_portal = PortalFactory.from_url(args.exit + "/exit")

    if args.remote:
        dst, dst_port = args.remote.split(':')
        dst_port = int(dst_port)
        tun = Tunnel(enter_portal, exit_portal, (dst, dst_port))
    else:
        tun = Tunnel(enter_portal, exit_portal)
    tun.run()


if __name__ == "__main__":
    tunnel_main()

