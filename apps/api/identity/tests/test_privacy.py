import io
from datetime import timedelta
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from identity.models import AbuseBucket, Membership, Scan, ScanReport, Site
from identity.services import create_user_workspace
from identity.worker import claim_scan, publish_report


class PrivacyTests(APITestCase):
    def setUp(self):
        import tempfile
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        config = override_settings(DELETION_LEDGER_PATH=self.temp.name + '/deletions.jsonl', DELETION_LEDGER_KEY='test-only-deletion-ledger-key-with-32-characters')
        config.enable(); self.addCleanup(config.disable)
        self.user, self.org = create_user_workspace(email='privacy@example.com', password='Strong-pass-2026!', display_name='Privacy', account_type='platform_developer')
        self.site = Site.objects.create(organization=self.org, display_name='Site', normalized_url='https://example.com/')
        self.scan = Scan.objects.create(organization=self.org, site=self.site, idempotency_key='privacy-request-0001')
        self.client.force_authenticate(self.user)
        self.url = reverse('scan-detail', args=[self.scan.id])

    def test_owner_deletes_snapshot_and_scan_and_read_is_now_404(self):
        publish_report(claim_scan(), {'engineVersion': '4.13.0', 'pages': []})
        self.assertEqual(self.client.delete(self.url).status_code, 204)
        self.assertFalse(Scan.objects.exists())
        self.assertFalse(ScanReport.objects.exists())
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.get(reverse('scan-report', args=[self.scan.id])).status_code, 404)
        self.assertTrue(Site.objects.filter(id=self.site.id).exists())

    def test_deleting_running_scan_fences_late_worker_and_does_not_recreate_report(self):
        claimed = claim_scan()
        self.assertEqual(self.client.delete(self.url).status_code, 204)
        with self.assertRaises(ValueError):
            publish_report(claimed, {'engineVersion': '4.13.0', 'pages': []})
        self.assertFalse(ScanReport.objects.exists())

    def test_only_owner_can_delete_and_other_tenant_gets_404(self):
        for role in ('viewer', 'member'):
            Membership.objects.filter(user=self.user).update(role=role)
            self.assertEqual(self.client.delete(self.url).status_code, 403)
        other, _ = create_user_workspace(email='other-privacy@example.com', password='Strong-pass-2026!', display_name='Other', account_type='platform_developer')
        self.client.force_authenticate(other)
        self.assertEqual(self.client.delete(self.url).status_code, 404)
        self.assertTrue(Scan.objects.filter(id=self.scan.id).exists())

    @override_settings(SCAN_RETENTION_DAYS=30)
    def test_retention_removes_old_terminal_jobs_but_preserves_active_and_recent(self):
        from identity.privacy import purge_expired
        old = timezone.now() - timedelta(days=31)
        ids = {}
        for state in ('completed', 'failed', 'cancelled', 'queued', 'running'):
            scan = Scan.objects.create(organization=self.org, site=self.site, idempotency_key='retention-' + state, status=state, completed_at=old if state not in ('queued', 'running') else None)
            Scan.objects.filter(id=scan.id).update(requested_at=old)
            ids[state] = scan.id
        ScanReport.objects.create(scan_id=ids['completed'], engine_version='4.13.0', payload={'private': 'screenshot and evidence'})
        fresh = Scan.objects.create(organization=self.org, site=self.site, idempotency_key='fresh-completed-0001', status='completed', completed_at=timezone.now())
        result = purge_expired()
        self.assertEqual(result['scansDeleted'], 3)
        self.assertFalse(ScanReport.objects.exists())
        self.assertTrue(Scan.objects.filter(id=fresh.id).exists())
        for state in ('queued', 'running'):
            self.assertTrue(Scan.objects.filter(id=ids[state]).exists())

    def test_expired_abuse_identities_are_removed_but_mutex_and_active_windows_remain(self):
        from identity.privacy import purge_expired
        old = timezone.now() - timedelta(days=8)
        for scope in ('scan_capacity', 'scan_ip', 'auth_login'):
            AbuseBucket.objects.create(scope=scope, key=scope, resets_at=old)
        AbuseBucket.objects.create(scope='api_ip', key='recent', resets_at=timezone.now() + timedelta(seconds=60))
        self.assertEqual(purge_expired()['bucketsDeleted'], 2)
        self.assertTrue(AbuseBucket.objects.filter(scope='scan_capacity').exists())
        self.assertTrue(AbuseBucket.objects.filter(key='recent').exists())

    def test_command_is_dry_run_by_default_and_requires_apply_to_delete(self):
        from django.core.management import call_command
        Scan.objects.filter(id=self.scan.id).update(status='failed', completed_at=timezone.now() - timedelta(days=31))
        out = io.StringIO()
        call_command('purge_expired_data', stdout=out)
        self.assertTrue(Scan.objects.exists())
        self.assertIn('dryRun', out.getvalue())
        call_command('purge_expired_data', apply=True, stdout=io.StringIO())
        self.assertFalse(Scan.objects.exists())

    def test_retention_is_bounded_and_catches_legacy_terminal_jobs_without_timestamp(self):
        from identity.privacy import purge_expired
        Scan.objects.filter(id=self.scan.id).update(status='failed', requested_at=timezone.now() - timedelta(days=31))
        for i in range(2):
            scan = Scan.objects.create(organization=self.org, site=self.site, idempotency_key=f'old-terminal-job-{i}', status='failed')
            Scan.objects.filter(id=scan.id).update(requested_at=timezone.now() - timedelta(days=31))
        self.assertEqual(purge_expired(batch_size=2)['scansDeleted'], 2)
        self.assertEqual(Scan.objects.count(), 1)

    def test_sensitive_api_responses_disable_browser_caching(self):
        self.assertIn('no-store', self.client.get(self.url).get('Cache-Control', ''))
