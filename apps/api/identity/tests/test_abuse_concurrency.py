from concurrent.futures import ThreadPoolExecutor
from unittest import skipUnless
from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase, override_settings
from rest_framework.exceptions import Throttled
from identity.abuse import enqueue_scan
from identity.models import AbuseBucket, Scan, Site
from identity.services import create_user_workspace


@skipUnless(connection.vendor == 'postgresql', 'Admissão concorrente exige PostgreSQL; job api do CI.')
@override_settings(SCAN_ACTIVE_GLOBAL_LIMIT=1)
class ConcurrentAdmissionTests(TransactionTestCase):
    def test_two_process_connections_cannot_exceed_global_queue_capacity(self):
        user, org = create_user_workspace(email='admission@example.com', password='Strong-pass-2026!', display_name='Admission', account_type='platform_developer')
        site = Site.objects.create(organization=org, display_name='Site', normalized_url='https://example.com/')

        def submit(index):
            close_old_connections()
            try:
                return str(enqueue_scan(user, site, f'concurrent-budget-{index:016d}', '127.0.0.1').id)
            except Throttled:
                return None
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, range(2)))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(Scan.objects.count(), 1)
        self.assertEqual(AbuseBucket.objects.get(scope='scan_user').count, 1)

    @override_settings(SCAN_ACTIVE_GLOBAL_LIMIT=10, SCAN_RATE_LIMITS={'user': 1, 'organization': 30, 'domain': 20, 'ip': 30})
    def test_concurrent_budget_and_idempotent_replay(self):
        user, org = create_user_workspace(email='budget-race@example.com', password='Strong-pass-2026!', display_name='Budget', account_type='platform_developer')
        site = Site.objects.create(organization=org, display_name='Site', normalized_url='https://example.com/')
        for same_key in (False, True):
            with self.subTest(same_key=same_key):
                Scan.objects.all().delete()
                AbuseBucket.objects.all().delete()

                def submit(index):
                    close_old_connections()
                    try:
                        key = 'same-key-0000000001' if same_key else f'different-key-{index:016d}'
                        return str(enqueue_scan(user, site, key, '127.0.0.1').id)
                    except Throttled:
                        return None
                    finally:
                        connections.close_all()

                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(submit, range(2)))
                self.assertEqual(sum(result is not None for result in results), 2 if same_key else 1)
                self.assertEqual(Scan.objects.count(), 1)
                self.assertEqual(AbuseBucket.objects.get(scope='scan_user').count, 1)
