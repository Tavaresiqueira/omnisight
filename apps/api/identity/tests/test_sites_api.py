import socket
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from identity.models import Membership, Organization, User


class SiteApiTests(APITestCase):
    def setUp(self):
        dns = patch(
            "identity.ssrf.socket.getaddrinfo",
            return_value=[
                (
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                    "",
                    ("93.184.216.34", 443),
                )
            ],
        )
        dns.start()
        self.addCleanup(dns.stop)
        self.user = User.objects.create_user(
            email="site-owner@example.com",
            password="Strong-pass-2026!",
            display_name="Site Owner",
            account_type=User.AccountType.PLATFORM_DEVELOPER,
        )
        self.organization = Organization.objects.create(
            name="Owner Workspace",
            slug="site-owner-workspace",
            account_type=self.user.account_type,
        )
        Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role=Membership.Role.OWNER,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="Strong-pass-2026!",
            display_name="Other User",
            account_type=User.AccountType.PLATFORM_DEVELOPER,
        )
        self.other_organization = Organization.objects.create(
            name="Other Workspace",
            slug="other-workspace",
            account_type=self.other_user.account_type,
        )
        Membership.objects.create(
            user=self.other_user,
            organization=self.other_organization,
            role=Membership.Role.OWNER,
        )
        self.client.force_authenticate(self.user)

    def test_create_site_normalizes_https_url(self):
        response = self.client.post(
            reverse("sites"),
            {"url": " HTTPS://Example.COM:443/docs#intro ", "displayName": "Documentação"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["normalizedUrl"], "https://example.com/docs")
        self.assertEqual(response.data["displayName"], "Documentação")
        self.assertRegex(response.data["id"], r"^[0-9a-f-]{36}$")
        self.assertTrue(response.data["createdAt"])
        self.assertEqual(
            set(response.data),
            {"id", "displayName", "normalizedUrl", "createdAt"},
        )

    def test_rejects_non_https_and_malformed_urls_with_problem_response(self):
        for url in ["http://example.com", "javascript:alert(1)", "https:///missing-host"]:
            with self.subTest(url=url):
                response = self.client.post(
                    reverse("sites"),
                    {"url": url, "displayName": "Site"},
                    format="json",
                )

                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.data["code"], "INVALID_URL")
                self.assertIn("https://", response.data["message"])
                self.assertTrue(response.data["correlationId"])

    def test_rejects_urls_with_embedded_credentials(self):
        response = self.client.post(
            reverse("sites"),
            {"url": "https://user:secret@example.com", "displayName": "Site"},
            format="json",
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data["code"], "INVALID_URL")

    def test_rejects_local_and_private_scan_destinations(self):
        for url in ["https://localhost", "https://10.0.0.1", "https://[::1]"]:
            with self.subTest(url=url):
                response = self.client.post(
                    reverse("sites"),
                    {"url": url, "displayName": "Site local"},
                    format="json",
                )

                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.data["code"], "DESTINATION_NOT_ALLOWED")

    def test_rejects_hostname_with_a_private_dns_answer(self):
        with patch(
            "identity.ssrf.socket.getaddrinfo",
            return_value=[
                (
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                    "",
                    ("10.0.0.8", 443),
                )
            ],
        ):
            response = self.client.post(
                reverse("sites"),
                {"url": "https://private.example", "displayName": "Site privado"},
                format="json",
            )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data["code"], "DESTINATION_NOT_ALLOWED")

    def test_duplicate_normalized_url_returns_conflict(self):
        payload = {"url": "https://example.com", "displayName": "Site"}
        first = self.client.post(reverse("sites"), payload, format="json")
        duplicate = self.client.post(
            reverse("sites"),
            {"url": "HTTPS://EXAMPLE.COM:443/", "displayName": "Outro nome"},
            format="json",
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(duplicate.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(duplicate.data["code"], "SITE_ALREADY_EXISTS")
        self.assertTrue(duplicate.data["correlationId"])

    def test_list_is_scoped_to_authenticated_organization(self):
        self.client.post(
            reverse("sites"),
            {"url": "https://mine.example", "displayName": "Meu site"},
            format="json",
        )
        self.client.force_authenticate(self.other_user)
        self.client.post(
            reverse("sites"),
            {"url": "https://mine.example", "displayName": "Mesmo URL em outra organização"},
            format="json",
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("sites"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([site["displayName"] for site in response.data["items"]], ["Meu site"])

    def test_sites_endpoint_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse("sites"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
