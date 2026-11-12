import http.client
import ipaddress
import socket
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit


MAX_REDIRECTS = 5
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 10
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
METADATA_HOSTS = {
    "metadata",
    "metadata.google.internal",
    "metadata.azure.internal",
    "metadata.aws.internal",
    "instance-data",
}
IPV6_TRANSITION_NETWORKS = (
    ipaddress.ip_network("64:ff9b::/96"),
    ipaddress.ip_network("64:ff9b:1::/48"),
    ipaddress.ip_network("2002::/16"),
    ipaddress.ip_network("2001::/32"),
)


class DestinationBlocked(ValueError):
    """Raised when a URL could reach a non-public or unvalidated destination."""


@dataclass(frozen=True)
class PublicDestination:
    url: str
    hostname: str
    port: int
    addresses: tuple[str, ...]

    @property
    def request_target(self):
        parts = urlsplit(self.url)
        return urlunsplit(("", "", parts.path or "/", parts.query, ""))


@dataclass(frozen=True)
class SafeFetchResponse:
    final_url: str
    status: int
    headers: dict[str, str]
    body: bytes
    redirects: int


def _public_ip(address):
    if "%" in address:
        raise DestinationBlocked("Endereços IPv6 com identificador de interface não são permitidos.")
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError as error:
        raise DestinationBlocked("O DNS retornou um endereço IP inválido.") from error
    if isinstance(parsed, ipaddress.IPv6Address) and parsed.ipv4_mapped:
        parsed = parsed.ipv4_mapped
    elif isinstance(parsed, ipaddress.IPv6Address) and any(
        parsed in network for network in IPV6_TRANSITION_NETWORKS
    ):
        raise DestinationBlocked("Túneis IPv6 e endereços de tradução não são permitidos.")
    if not parsed.is_global:
        raise DestinationBlocked("O destino resolve para uma rede privada ou reservada.")
    return str(parsed)


def resolve_public_destination(url):
    try:
        parts = urlsplit(url)
        hostname = parts.hostname
        port = parts.port or 443
    except (AttributeError, TypeError, ValueError) as error:
        raise DestinationBlocked("Informe uma URL HTTPS válida.") from error

    if parts.scheme.lower() != "https" or not hostname:
        raise DestinationBlocked("Somente URLs HTTPS com hostname são permitidas.")
    if parts.username is not None or parts.password is not None:
        raise DestinationBlocked("URLs com credenciais embutidas não são permitidas.")
    if port != 443:
        raise DestinationBlocked("Somente conexões HTTPS na porta 443 são permitidas.")

    try:
        normalized_host = hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as error:
        raise DestinationBlocked("O hostname da URL é inválido.") from error

    if (
        normalized_host in METADATA_HOSTS | {"localhost", "local"}
        or normalized_host.endswith((".localhost", ".local", ".internal"))
    ):
        raise DestinationBlocked("Hostnames locais ou de metadata não são permitidos.")

    try:
        literal = ipaddress.ip_address(normalized_host)
    except ValueError:
        literal = None

    if literal:
        addresses = (_public_ip(str(literal)),)
    else:
        try:
            records = socket.getaddrinfo(
                normalized_host,
                port,
                type=socket.SOCK_STREAM,
            )
        except OSError as error:
            raise DestinationBlocked("Não foi possível resolver o hostname da URL.") from error

        if not records:
            raise DestinationBlocked("O hostname da URL não possui endereços públicos.")
        # Reject the host if any answer is unsafe; picking only its public answer
        # would leave room for DNS rotation or rebinding to an internal address.
        addresses = tuple(sorted({_public_ip(record[4][0]) for record in records}))

    host_for_url = f"[{normalized_host}]" if ":" in normalized_host else normalized_host
    normalized_url = urlunsplit(
        ("https", host_for_url, parts.path or "/", parts.query, "")
    )
    return PublicDestination(normalized_url, normalized_host, port, addresses)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, destination, timeout):
        super().__init__(destination.hostname, destination.port, timeout=timeout)
        self.addresses = destination.addresses

    def connect(self):
        last_error = None
        for address in self.addresses:
            raw_socket = None
            try:
                raw_socket = socket.create_connection(
                    (address, self.port),
                    self.timeout,
                    self.source_address,
                )
                self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)
                return
            except OSError as error:
                last_error = error
                if raw_socket:
                    raw_socket.close()
        if last_error:
            raise last_error
        raise DestinationBlocked("Não há endereço público validado para conexão.")


def _request_once(destination, timeout, max_response_bytes):
    connection = _PinnedHTTPSConnection(destination, timeout)
    try:
        connection.request(
            "GET",
            destination.request_target,
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Encoding": "identity",
                "Connection": "close",
                "User-Agent": "OmniSight-Scanner/0.1",
            },
        )
        response = connection.getresponse()
        headers = response.getheaders()
        if response.status in REDIRECT_STATUSES:
            return response.status, headers, b""
        content_length = response.getheader("Content-Length")
        if content_length:
            try:
                declared_length = int(content_length)
            except ValueError:
                declared_length = None
            if declared_length is not None and declared_length > max_response_bytes:
                raise DestinationBlocked("A resposta excedeu o limite permitido para o scan.")

        deadline = time.monotonic() + timeout
        chunks = []
        received = 0
        while True:
            remaining_time = deadline - time.monotonic()
            if remaining_time <= 0:
                raise DestinationBlocked("A resposta excedeu o tempo permitido para o scan.")
            connection.sock.settimeout(remaining_time)
            chunk = response.read(min(64 * 1024, max_response_bytes + 1 - received))
            if not chunk:
                break
            chunks.append(chunk)
            received += len(chunk)
            if received > max_response_bytes:
                raise DestinationBlocked("A resposta excedeu o limite permitido para o scan.")
        return response.status, headers, b"".join(chunks)
    finally:
        connection.close()


def fetch_public_url(
    url,
    *,
    max_redirects=MAX_REDIRECTS,
    max_response_bytes=MAX_RESPONSE_BYTES,
    timeout=REQUEST_TIMEOUT_SECONDS,
    allowed_hostname=None,
):
    """Fetch an HTTPS page while pinning every connection to validated DNS."""
    current_url = url
    redirects = 0

    while True:
        if allowed_hostname is not None:
            redirect_host = urlsplit(current_url).hostname
            if not redirect_host or redirect_host.rstrip(".").encode("idna").decode("ascii").lower() != allowed_hostname:
                raise DestinationBlocked("O redirecionamento saiu do domínio autorizado.")
        destination = resolve_public_destination(current_url)
        response_status, raw_headers, body = _request_once(
            destination,
            timeout,
            max_response_bytes,
        )
        headers = {name.lower(): value for name, value in raw_headers}

        if response_status not in REDIRECT_STATUSES:
            return SafeFetchResponse(
                final_url=destination.url,
                status=response_status,
                headers=headers,
                body=body,
                redirects=redirects,
            )

        location = headers.get("location")
        if not location:
            raise DestinationBlocked("O redirecionamento não informou um destino válido.")
        if redirects >= max_redirects:
            raise DestinationBlocked("A página excedeu o limite de redirecionamentos.")

        current_url = urljoin(destination.url, location)
        redirects += 1
