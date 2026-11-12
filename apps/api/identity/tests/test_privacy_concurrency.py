from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from unittest import skipUnless
from django.db import close_old_connections, connection, connections, transaction
from django.test import TransactionTestCase
from django.utils import timezone
from identity.models import Scan, ScanReport, Site
from identity.privacy import purge_expired
from identity.services import create_user_workspace
from identity.worker import claim_scan, publish_report


@skipUnless(connection.vendor == 'postgresql', 'Concorrência de descarte exige PostgreSQL; job api do CI.')
class ConcurrentPrivacyTests(TransactionTestCase):
    def setUp(self):
        _, org = create_user_workspace(email='privacy-race@example.com', password='Strong-pass-2026!', display_name='Privacy', account_type='platform_developer')
        site = Site.objects.create(organization=org, display_name='Site', normalized_url='https://example.com/')
        self.scan = Scan.objects.create(organization=org, site=site, idempotency_key='privacy-race-00001')

    def test_late_publisher_waits_for_deletion_and_cannot_resurrect_report(self):
        claimed = claim_scan()
        started = Event()

        def publish():
            close_old_connections()
            try:
                started.set()
                publish_report(claimed, {'engineVersion': '4.13.0', 'pages': []})
                return 'published'
            except ValueError:
                return 'fenced'
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                locked = Scan.objects.select_for_update().get(id=self.scan.id)
                locked.delete()
                result = pool.submit(publish)
                self.assertTrue(started.wait(5))
            self.assertEqual(result.result(timeout=10), 'fenced')
        self.assertFalse(ScanReport.objects.exists())

    def test_retention_skips_a_locked_scan_then_disposes_it_after_commit(self):
        Scan.objects.filter(id=self.scan.id).update(status='failed', completed_at=timezone.now() - timedelta(days=31))

        def purge():
            close_old_connections()
            try:
                return purge_expired()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                Scan.objects.select_for_update().get(id=self.scan.id)
                result = pool.submit(purge).result(timeout=10)
                self.assertEqual(result['scansDeleted'], 0)
        self.assertEqual(purge_expired()['scansDeleted'], 1)
