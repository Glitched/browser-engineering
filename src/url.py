import gzip
import socket
import ssl
import time
from dataclasses import dataclass

from entities import entities

# (host, port) -> socket
sockets: dict[tuple[str, int], socket.socket] = {}


@dataclass
class CacheEntry:
    content: str
    expires: float


cache: dict[str, CacheEntry] = {}


class URL:
    scheme: str
    host: str
    path: str
    port: int
    view_source: bool = False
    headers: dict[str, str] = {
        "User-Agent": "Slama/0.1",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip",
    }
    redirects: list[str]

    def __init__(self, url: str, redirects: list[str] = list()):
        self.redirects = redirects

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

    def get_url_string(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}{self.path}"

    def request(self) -> str:
        if self.get_url_string() in cache:
            entry = cache[self.get_url_string()]
            if entry.expires > time.time():
                return entry.content
            else:
                del cache[self.get_url_string()]

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

        response = s.makefile("rb")
        statusline = response.readline().decode("utf8")
        _version, status, _explanation = statusline.split(" ", 2)

        response_headers: dict[str, str] = {}
        while True:
            line = response.readline().decode("utf8")
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        content_encoding = response_headers.get("content-encoding", "")
        transfer_encoding = response_headers.get("transfer-encoding", "")
        if transfer_encoding == "chunked":
            body_bytes = b""
            while True:
                chunk_length = int(response.readline().decode("utf8"), 16)
                body_bytes += response.read(chunk_length)
                response.read(2)
                if chunk_length == 0:
                    break
        else:
            content_length = int(response_headers["content-length"])
            body_bytes = response.read(content_length)

        if content_encoding == "gzip":
            content = gzip.decompress(body_bytes).decode("utf8")
        else:
            content = body_bytes.decode("utf8")

        if status == "301" or status == "302":
            location = response_headers["location"]
            if location in self.redirects:
                raise Exception("Redirect loop")
            if len(self.redirects) > 10:
                raise Exception("Too many redirects")

            if location.startswith("/"):
                location = f"{self.scheme}://{self.host}:{self.port}{location}"

            return URL(location, self.redirects + [location]).request()

        cache_control = response_headers.get("cache-control", "")
        if (
            status == "200"
            and "no-store" not in cache_control
            and "no-cache" not in cache_control
            and "max-age" in cache_control
        ):
            max_age = int(cache_control.split("=")[1])
            cache[self.get_url_string()] = CacheEntry(content, time.time() + max_age)

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
        if (self.host, self.port) in sockets:
            return sockets[(self.host, self.port)]

        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )

        s.connect((self.host, self.port))
        sockets[(self.host, self.port)] = s

        return s
