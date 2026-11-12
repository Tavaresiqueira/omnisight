from concurrent.futures import ThreadPoolExecutor
from unittest import skipUnless
from django.db import connection,close_old_connections
from django.test import TransactionTestCase
from identity.models import Scan,Site
from identity.services import create_user_workspace
from identity.worker import claim_scan

@skipUnless(connection.vendor=='postgresql','Teste de concorrência real exige PostgreSQL; job api do CI.')
class ConcurrentClaimTests(TransactionTestCase):
    def test_two_consumers_claim_one_job_only_once(self):
        _,org=create_user_workspace(email='concurrent@example.com',password='Strong-pass-2026!',display_name='Concurrent',account_type='platform_developer')
        site=Site.objects.create(organization=org,display_name='Site',normalized_url='https://example.com/')
        Scan.objects.create(organization=org,site=site,idempotency_key='concurrent-key-0001')
        def claim():
            close_old_connections()
            try:
                scan=claim_scan()
                return str(scan.id) if scan else None
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:claim(),range(2)))
        self.assertEqual(len([r for r in results if r is not None]),1)
        self.assertEqual(Scan.objects.get().attempts,1)
