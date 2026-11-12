import socket
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from identity.ssrf import (
    DestinationBlocked,
    PublicDestination,
    _PinnedHTTPSConnection,
    fetch_public_url,
    resolve_public_destination,
)


def dns_result(address, family=socket.AF_INET):
    sockaddr = (address, 443) if family == socket.AF_INET else (address, 443, 0, 0)
    return [(family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)]


class PublicDestinationTests(SimpleTestCase):
    def test_accepts_public_ipv4_and_ipv6_literals(self):
        ipv4 = resolve_public_destination("https://8.8.8.8/")
        ipv6 = resolve_public_destination("https://[2606:4700:4700::1111]/")

        self.assertEqual(ipv4.addresses, ("8.8.8.8",))
        self.assertEqual(ipv6.addresses, ("2606:4700:4700::1111",))

    def test_blocks_local_metadata_and_non_global_ip_destinations(self):
        for url in [
            "https://localhost/",
            "https://service.localhost/",
            "https://metadata.google.internal/",
            "https://10.0.0.1/",
            "https://169.254.169.254/latest/meta-data/",
            "https://[::1]/",
            "https://[fd00::1]/",
            "https://192.0.2.1/",
            "https://100.100.100.200/",
            "https://[::ffff:127.0.0.1]/",
            "https://[64:ff9b::a00:1]/",
            "https://public.example:8443/",
        ]:
            with self.subTest(url=url), self.assertRaises(DestinationBlocked):
                resolve_public_destination(url)

    @patch("identity.ssrf.socket.getaddrinfo")
    def test_rejects_host_when_any_dns_answer_is_non_public(self, getaddrinfo):
        getaddrinfo.return_value = dns_result("93.184.216.34") + dns_result("10.0.0.4")

        with self.assertRaises(DestinationBlocked):
            resolve_public_destination("https://mixed.example/")

    @patch("identity.ssrf.socket.getaddrinfo")
    @patch("identity.ssrf._request_once")
    def test_pins_connection_to_the_address_that_was_validated(self, request_once, getaddrinfo):
        getaddrinfo.side_effect = [
            dns_result("93.184.216.34"),
            dns_result("127.0.0.1"),
        ]
        request_once.return_value = (200, [("Content-Type", "text/html")], b"ok")

        response = fetch_public_url("https://changing.example/")

        self.assertEqual(response.body, b"ok")
        self.assertEqual(request_once.call_args.args[0].addresses, ("93.184.216.34",))
        getaddrinfo.assert_called_once()

    @patch("identity.ssrf.socket.getaddrinfo")
    @patch("identity.ssrf._request_once")
    def test_revalidates_redirect_destination_before_requesting_it(self, request_once, getaddrinfo):
        getaddrinfo.return_value = dns_result("93.184.216.34")
        request_once.return_value = (
            302,
            [("Location", "https://127.0.0.1/admin")],
            b"",
        )

        with self.assertRaises(DestinationBlocked):
            fetch_public_url("https://public.example/")

        request_once.assert_called_once()

    @patch("identity.ssrf.socket.getaddrinfo")
    @patch("identity.ssrf._request_once")
    def test_blocks_https_downgrade_redirects(self, request_once, getaddrinfo):
        getaddrinfo.return_value = dns_result("93.184.216.34")
        request_once.return_value = (
            302,
            [("Location", "http://public.example/")],
            b"",
        )

        with self.assertRaises(DestinationBlocked):
            fetch_public_url("https://public.example/")

        request_once.assert_called_once()

    @patch("identity.ssrf.socket.getaddrinfo")
    @patch("identity.ssrf._request_once")
    def test_resolves_and_pins_each_allowed_redirect_hop(self, request_once, getaddrinfo):
        getaddrinfo.side_effect = [dns_result("93.184.216.34"), dns_result("1.1.1.1")]
        request_once.side_effect = [
            (301, [("Location", "/next")], b""),
            (200, [("Content-Type", "text/html")], b"page"),
        ]

        response = fetch_public_url("https://start.example/")

        self.assertEqual(response.final_url, "https://start.example/next")
        self.assertEqual(response.redirects, 1)
        self.assertEqual(request_once.call_count, 2)
        self.assertEqual(request_once.call_args_list[1].args[0].addresses, ("1.1.1.1",))

    @patch("identity.ssrf.socket.getaddrinfo")
    def test_dns_resolution_failure_is_denied(self, getaddrinfo):
        getaddrinfo.side_effect = socket.gaierror("name not known")

        with self.assertRaises(DestinationBlocked):
            resolve_public_destination("https://unresolved.example/")

    def test_connection_uses_validated_ip_while_preserving_tls_hostname(self):
        destination = PublicDestination(
            url="https://public.example/",
            hostname="public.example",
            port=443,
            addresses=("93.184.216.34",),
        )
        connection = _PinnedHTTPSConnection(destination, timeout=5)
        raw_socket = Mock()
        tls_socket = Mock()

        with (
            patch("identity.ssrf.socket.create_connection", return_value=raw_socket) as connect,
            patch.object(connection._context, "wrap_socket", return_value=tls_socket) as wrap,
        ):
            connection.connect()

        connect.assert_called_once_with(("93.184.216.34", 443), 5, None)
        wrap.assert_called_once_with(raw_socket, server_hostname="public.example")
        connection.close()
