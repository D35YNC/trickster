from urllib.parse import urlparse

from trickster.tunnel import Portal
from trickster.tunnel.tcp import TCPPortal
from trickster.tunnel.icmp import ICMPPortal


class PortalFactory:
    @staticmethod
    def from_url(url: str) -> Portal:
        u = urlparse(url)
        dst = None
        if ':' in u.netloc:
            ip, port = u.netloc.split(':', 1)
            dst = (ip, int(port))
        elif u.netloc:
            dst = (u.netloc, None)
        match u.scheme.lower():
            case "tcp":
                if u.path == "/enter":
                    return TCPPortal(bind=dst, is_enter=True)
                else:
                    return TCPPortal(endpoint=dst, is_enter=False)
            case "icmp":
                if u.path == "/enter":
                    return ICMPPortal(endpoint=dst, is_enter=True)
                else:
                    return ICMPPortal(endpoint=dst, is_enter=False)
