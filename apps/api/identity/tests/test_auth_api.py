from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from identity.models import Membership, Organization, User


class RegistrationTests(APITestCase):
    def test_registration_creates_owner_and_personal_organization(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "dev@example.com",
                "password": "Strong-pass-2026!",
                "display_name": "Dev Exemplo",
                "account_type": User.AccountType.PLATFORM_DEVELOPER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="dev@example.com")
        membership = Membership.objects.get(user=user)
        self.assertEqual(membership.role, Membership.Role.OWNER)
        self.assertEqual(membership.organization.account_type, user.account_type)
        self.assertEqual(response.data["user"]["account_type"], "platform_developer")
        self.assertEqual(response.data["organization"]["id"], str(membership.organization_id))
        self.assertTrue(response.data["token"])

    def test_registration_accepts_extension_user(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "extension@example.com",
                "password": "Strong-pass-2026!",
                "display_name": "Pessoa Usuária",
                "account_type": User.AccountType.EXTENSION_USER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["account_type"], "extension_user")

    def test_registration_rejects_unknown_account_type(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "invalid@example.com",
                "password": "Strong-pass-2026!",
                "display_name": "Perfil Inválido",
                "account_type": "administrator",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("account_type", response.data)

    def test_registration_treats_email_as_case_insensitive(self):
        User.objects.create_user(
            email="person@example.com",
            password="Strong-pass-2026!",
            display_name="Pessoa",
            account_type=User.AccountType.EXTENSION_USER,
        )

        response = self.client.post(
            reverse("register"),
            {
                "email": "PERSON@example.com",
                "password": "Another-pass-2026!",
                "display_name": "Outra Pessoa",
                "account_type": User.AccountType.EXTENSION_USER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)


class AuthenticationAndIsolationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="Strong-pass-2026!",
            display_name="Owner",
            account_type=User.AccountType.PLATFORM_DEVELOPER,
        )
        self.organization = Organization.objects.create(
            name="Owner Workspace",
            slug="owner-workspace",
            account_type=self.user.account_type,
        )
        Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role=Membership.Role.OWNER,
        )
        self.other_organization = Organization.objects.create(
            name="Another Workspace",
            slug="another-workspace",
            account_type=User.AccountType.EXTENSION_USER,
        )

    def login(self):
        response = self.client.post(
            reverse("login"),
            {"email": self.user.email, "password": "Strong-pass-2026!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")

    def test_login_and_me_return_authenticated_identity(self):
        self.login()

        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], self.user.email)
        self.assertEqual(response.data["organization"]["id"], str(self.organization.id))

    def test_demo_login_only_issues_a_token_for_the_requested_demo_profile(self):
        demo = User.objects.create_user(
            email="extension.demo@omnisight.local",
            password="Strong-pass-2026!",
            display_name="Demo Extensão",
            account_type=User.AccountType.EXTENSION_USER,
            is_demo=True,
        )
        demo_org = Organization.objects.create(
            name="Demo Extension Workspace",
            slug="demo-extension-workspace",
            account_type=demo.account_type,
        )
        Membership.objects.create(
            user=demo,
            organization=demo_org,
            role=Membership.Role.OWNER,
        )

        response = self.client.post(
            reverse("demo-login"),
            {"account_type": User.AccountType.EXTENSION_USER},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["id"], str(demo.id))
        self.assertEqual(response.data["user"]["account_type"], "extension_user")
        self.assertTrue(response.data["token"])

    def test_demo_login_does_not_authenticate_regular_accounts(self):
        response = self.client.post(
            reverse("demo-login"),
            {"account_type": User.AccountType.PLATFORM_DEVELOPER},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_read_own_organization(self):
        self.login()

        response = self.client.get(
            reverse("organization-detail", args=[self.organization.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_read_another_organization(self):
        self.login()

        response = self.client.get(
            reverse("organization-detail", args=[self.other_organization.id])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
