import hashlib
import tempfile
from pathlib import Path
from django.test import override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from identity.models import Membership, Organization, Scan, ScanReport, Site, User
from identity.services import create_user_workspace


class AccountLifecycleTests(APITestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.ledger = Path(self.temp.name) / 'deletions.jsonl'
        config = override_settings(DELETION_LEDGER_PATH=str(self.ledger), DELETION_LEDGER_KEY='test-only-ledger-key-with-at-least-32-characters')
        config.enable(); self.addCleanup(config.disable)
        self.password = 'Strong-pass-2026!'
        self.user, self.org = create_user_workspace(email='closure@example.com', password=self.password, display_name='Closure', account_type='platform_developer')
        self.site = Site.objects.create(organization=self.org, display_name='Site', normalized_url='https://example.com/')
        self.scan = Scan.objects.create(organization=self.org, site=self.site, idempotency_key='closure-request-0001', status='completed')
        ScanReport.objects.create(scan=self.scan, engine_version='4.13.0', payload={'pages': []})
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def close(self, password=None, confirmation='ENCERRAR MINHA CONTA'):
        return self.client.post(reverse('close-account'), {'password': password or self.password, 'confirmation': confirmation}, format='json')

    def test_personal_account_closure_deletes_workspace_reports_and_token(self):
        self.assertEqual(self.close().status_code, 204)
        self.assertFalse(User.objects.exists()); self.assertFalse(Organization.objects.exists())
        self.assertFalse(ScanReport.objects.exists()); self.assertFalse(Token.objects.exists())
        self.assertEqual(self.client.get(reverse('me')).status_code, 401)
        text = self.ledger.read_text(); self.assertNotIn('closure@example.com', text)
        self.assertNotIn(self.token.key, text)

    def test_wrong_password_or_confirmation_never_deletes_or_records_intent(self):
        self.assertEqual(self.close(password='wrong').status_code, 400)
        self.assertEqual(self.close(confirmation='no').status_code, 400)
        self.assertTrue(User.objects.exists()); self.assertFalse(self.ledger.exists())

    def test_only_owner_of_shared_workspace_must_handle_it_explicitly(self):
        other, _ = create_user_workspace(email='member@example.com', password=self.password, display_name='Member', account_type='platform_developer')
        Membership.objects.create(user=other, organization=self.org, role='member')
        self.assertEqual(self.close().status_code, 409)
        self.assertTrue(User.objects.filter(id=self.user.id).exists())
        self.assertFalse(self.ledger.exists())

    def test_coowner_account_can_leave_without_deleting_other_users_workspace(self):
        other, _ = create_user_workspace(email='coowner@example.com', password=self.password, display_name='Coowner', account_type='platform_developer')
        Membership.objects.create(user=other, organization=self.org, role='owner')
        self.assertEqual(self.close().status_code, 204)
        self.assertTrue(Organization.objects.filter(id=self.org.id).exists())
        self.assertTrue(ScanReport.objects.exists()); self.assertTrue(User.objects.filter(id=other.id).exists())

    def test_owner_closes_named_workspace_without_deleting_other_accounts(self):
        other, _ = create_user_workspace(email='member@example.com', password=self.password, display_name='Member', account_type='platform_developer')
        Membership.objects.create(user=other, organization=self.org, role='member')
        url = reverse('organization-detail', args=[self.org.id])
        self.assertEqual(self.client.post(url, {'password': self.password, 'confirmation': self.org.name}, format='json').status_code, 204)
        self.assertFalse(Organization.objects.filter(id=self.org.id).exists())
        self.assertTrue(User.objects.filter(id=other.id).exists()); self.assertTrue(User.objects.filter(id=self.user.id).exists())
        self.assertFalse(ScanReport.objects.exists())

    def test_member_cannot_close_workspace_and_export_omits_secrets(self):
        response = self.client.get(reverse('export-account'))
        self.assertEqual(response.status_code, 200)
        text = str(response.data)
        self.assertNotIn(self.user.password, text); self.assertNotIn(self.token.key, text)
        Membership.objects.filter(user=self.user).update(role='member')
        response = self.client.post(reverse('organization-detail', args=[self.org.id]), {'password': self.password, 'confirmation': self.org.name}, format='json')
        self.assertEqual(response.status_code, 403)

    @override_settings(DELETION_LEDGER_KEY='')
    def test_missing_durable_ledger_fails_closed_before_deletion(self):
        self.assertEqual(self.close().status_code, 503)
        self.assertTrue(User.objects.exists()); self.assertTrue(ScanReport.objects.exists())

    def test_reapply_ledger_suppresses_account_and_org_from_older_restore(self):
        from django.core.management import call_command
        from django.core.management.base import CommandError
        import io
        self.assertEqual(self.close().status_code, 204)
        # Reintroduce old backup identifiers, not a newly registered identity.
        restored = User.objects.create_user(id=self.user.id, email='closure@example.com', password=self.password, display_name='Restored', account_type='platform_developer')
        org = Organization.objects.create(id=self.org.id, name='Restored', slug='restored', account_type='platform_developer')
        Membership.objects.create(user=restored, organization=org, role='owner')
        digest = hashlib.sha256(self.ledger.read_bytes()).hexdigest()
        with self.assertRaises(CommandError):
            call_command('reapply_deletions', ledger=str(self.ledger), expected_sha256='0' * 64, stdout=io.StringIO())
        self.assertTrue(User.objects.exists())
        call_command('reapply_deletions', ledger=str(self.ledger), expected_sha256=digest, stdout=io.StringIO())
        self.assertTrue(User.objects.exists())  # Dry run is default.
        call_command('reapply_deletions', ledger=str(self.ledger), expected_sha256=digest, apply=True, stdout=io.StringIO())
        self.assertFalse(User.objects.exists()); self.assertFalse(Organization.objects.exists())
        call_command('reapply_deletions', ledger=str(self.ledger), expected_sha256=digest, apply=True, stdout=io.StringIO())

    def test_modified_ledger_is_rejected_even_with_matching_file_digest(self):
        from identity.deletion_ledger import append_deletions, read_deletions
        append_deletions([('scan', self.scan.id)])
        raw = self.ledger.read_bytes().replace(b'"scan"', b'"user"')
        self.ledger.write_bytes(raw)
        with self.assertRaises(ValueError):
            read_deletions(self.ledger, hashlib.sha256(raw).hexdigest())

    def test_concurrent_journal_writers_preserve_chain_and_incomplete_tail_is_rejected(self):
        from concurrent.futures import ThreadPoolExecutor
        from identity.deletion_ledger import append_deletions, read_deletions
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda target: append_deletions([('scan', target)]), [self.scan.id, self.site.id]))
        raw = self.ledger.read_bytes()
        self.assertEqual(len(read_deletions(self.ledger, hashlib.sha256(raw).hexdigest())), 2)
        self.assertEqual(self.ledger.stat().st_mode & 0o777, 0o600)
        self.ledger.write_bytes(raw[:-1])
        with self.assertRaises(ValueError):
            read_deletions(self.ledger, hashlib.sha256(raw[:-1]).hexdigest())

    def test_account_remains_usable_without_workspace_after_explicit_workspace_closure(self):
        url = reverse('organization-detail', args=[self.org.id])
        self.assertEqual(self.client.post(url, {'password': self.password, 'confirmation': self.org.name}, format='json').status_code, 204)
        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['organization']); self.assertIsNone(response.data['role'])
