from urllib.parse import urlparse

from trickster.tunnel import Portal
from trickster.tunnel.tcp import TCPPortal
from trickster.tunnel.icmp import ICMPPortal


class PortalFactory:
    @staticmethod
    def from_url(url: str) -> Portal:
        u = urlparse(url)
        match u.scheme.lower():
            case "tcp":
                if u.path == "/enter":
                    ip, port = u.netloc.split(':')
                    return TCPPortal(bind=(ip, int(port)))
                else:
                    return TCPPortal(endpoint=(ip, int(port)))
            case "icmp":
                if u.path == "/enter":
                    return ICMPPortal()
                else:
                    if ':' in u.netloc:
                        ip, port = u.netloc.split(':')
                    else:
                        ip = u.netloc
                        port = 0
                    return ICMPPortal(endpoint=(ip, int(port)))
