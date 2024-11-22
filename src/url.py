import socket
import ssl

from entities import entities


class URL:
    scheme: str
    host: str
    path: str
    port: int
    view_source: bool = False
    headers: dict[str, str] = {
        "User-Agent": "Slama/0.1",
        # "Connection": "Close",
    }

    # (host, port) -> socket
    sockets: dict[tuple[str, int], socket.socket] = {}

    def __init__(self, url: str):
        if url.startswith("view-source:"):
            self.view_source = True
            url = url[12:]

        if url.startswith("data:"):
            self.scheme = "data"
            _type, self.path = url.split(",", 1)
            return

        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file", "data"]
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        if self.scheme == "file":
            with open(self.path, "rb") as f:
                return f.read().decode("utf8")

        if self.scheme == "data":
            return self.path

        s = self.get_socket()

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        request = self.build_request()
        s.send(request.encode("utf8"))

        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        _version, _status, _explanation = statusline.split(" ", 2)

        response_headers: dict[str, str] = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        content_length = int(response_headers.get("content-length", "0"))
        content = response.read(content_length)

        if self.view_source:
            for entity, char in entities.items():
                content = content.replace(char, entity)

        return content

    def build_request(self):
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
        for header, value in self.headers.items():
            request += "{}: {}\r\n".format(header, value)
        request += "\r\n"
        return request

    def get_socket(self):
        if (self.host, self.port) in self.sockets:
            return self.sockets[(self.host, self.port)]

        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )

        s.connect((self.host, self.port))
        self.sockets[(self.host, self.port)] = s

        return s
