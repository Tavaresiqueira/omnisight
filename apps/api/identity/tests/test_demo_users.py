import os
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from identity.models import Membership, User


class SeedDemoUsersTests(TestCase):
    @patch.dict(os.environ, {"OMNISIGHT_DEMO_PASSWORD": "Demo-pass-2026!"})
    def test_command_creates_one_demo_for_each_account_type_and_is_idempotent(self):
        call_command("seed_demo_users")
        call_command("seed_demo_users")

        extension = User.objects.get(email="extension.demo@omnisight.local")
        developer = User.objects.get(email="developer.demo@omnisight.local")

        self.assertEqual(extension.account_type, User.AccountType.EXTENSION_USER)
        self.assertEqual(developer.account_type, User.AccountType.PLATFORM_DEVELOPER)
        self.assertTrue(extension.check_password("Demo-pass-2026!"))
        self.assertTrue(developer.check_password("Demo-pass-2026!"))
        self.assertEqual(Membership.objects.filter(user=extension).count(), 1)
        self.assertEqual(Membership.objects.filter(user=developer).count(), 1)
        self.assertEqual(User.objects.filter(is_demo=True).count(), 2)

