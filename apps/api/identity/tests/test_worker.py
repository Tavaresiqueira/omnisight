from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from identity.models import Scan, Site
from identity.services import create_user_workspace
from identity.worker import claim_scan, recover_expired, publish_report, process_next

class WorkerTests(TestCase):
    def setUp(self):
        _, self.org = create_user_workspace(email='worker@example.com',password='Strong-pass-2026!',display_name='Worker',account_type='platform_developer')
        self.site=Site.objects.create(organization=self.org,display_name='Site',normalized_url='https://example.com/')
        self.scan=Scan.objects.create(organization=self.org,site=self.site,idempotency_key='worker-key-00001')

    def test_claim_is_exclusive_and_has_fenced_lease(self):
        claimed=claim_scan()
        self.assertEqual(claimed.id,self.scan.id)
        self.assertEqual(claimed.attempts,1)
        self.assertIsNotNone(claimed.lease_token)
        self.assertGreater(claimed.lease_expires_at,timezone.now())
        self.assertIsNone(claim_scan())

    def test_expired_job_is_retried_and_stale_worker_cannot_publish(self):
        first=claim_scan()
        Scan.objects.filter(id=first.id).update(lease_expires_at=timezone.now()-timedelta(seconds=1))
        recover_expired();second=claim_scan()
        self.assertNotEqual(first.lease_token,second.lease_token)
        with self.assertRaises(ValueError):publish_report(first,{'engine':'axe-core','engineVersion':'4.13.0','pages':[]})
        self.assertEqual(Scan.objects.get(id=first.id).status,'running')

    def test_third_expiration_becomes_terminal_failure(self):
        for _ in range(3):
            claim_scan();Scan.objects.filter(id=self.scan.id).update(lease_expires_at=timezone.now()-timedelta(seconds=1));recover_expired()
        self.scan.refresh_from_db();self.assertEqual(self.scan.status,'failed');self.assertEqual(self.scan.attempts,3)
        self.assertIsNone(claim_scan())

    def test_report_publication_is_atomic_and_write_once(self):
        claimed=claim_scan();payload={'engine':'axe-core','engineVersion':'4.13.0','pages':[]}
        publish_report(claimed,payload)
        self.scan.refresh_from_db();self.assertEqual(self.scan.status,'completed');self.assertEqual(self.scan.report.payload,payload)
        with self.assertRaises(ValueError):publish_report(claimed,payload)
        report=self.scan.report;report.payload={}
        with self.assertRaises(ValueError):report.save()

    @patch('identity.worker.collect_and_analyze',side_effect=TimeoutError('contains private server detail'))
    def test_failure_is_recorded_without_exposing_internal_errors(self,analyze):
        self.assertTrue(process_next());self.scan.refresh_from_db()
        self.assertEqual(self.scan.status,'failed');self.assertEqual(self.scan.error_code,'SCAN_TIMEOUT');self.assertFalse(hasattr(self.scan,'report'))

    @patch('identity.worker.collect_and_analyze',return_value={'engine':'axe-core','engineVersion':'4.13.0','pages':[]})
    def test_consumer_completes_a_persisted_job(self,analyze):
        self.assertTrue(process_next());self.scan.refresh_from_db();self.assertEqual(self.scan.status,'completed')

    @patch('identity.pipeline.analyze_page')
    @patch('identity.pipeline.crawl')
    def test_collection_uses_safe_crawler_and_stores_hash_not_source(self,crawler,analyzer):
        from identity.ssrf import SafeFetchResponse
        from identity.pipeline import collect_and_analyze
        crawler.return_value=[SafeFetchResponse('https://example.com/',200,{'content-type':'text/html'},b'<h1>Private source</h1>',0)]
        analyzer.return_value={'engine':'axe-core','engineVersion':'4.13.0','mode':'offline-html','checks':[]}
        report=collect_and_analyze('https://example.com/')
        crawler.assert_called_once_with('https://example.com/',max_pages=1,max_depth=0,timeout=30)
        self.assertEqual(len(report['pages'][0]['htmlSha256']),64)
        self.assertNotIn('Private source',str(report))

    @patch('identity.worker.os.killpg')
    @patch('identity.worker.subprocess.Popen')
    def test_process_budget_covers_stalled_dns_and_drops_db_secrets(self,popen,killpg):
        import subprocess,signal
        from identity.worker import collect_and_analyze
        process=popen.return_value;process.pid=321;process.communicate.side_effect=[subprocess.TimeoutExpired('pipeline',90),(b'',b'')]
        with patch.dict('os.environ',{'DATABASE_URL':'private'}):
            with self.assertRaises(TimeoutError):collect_and_analyze('https://example.com/')
        self.assertNotIn('DATABASE_URL',popen.call_args.kwargs['env'])
        killpg.assert_called_once_with(321,signal.SIGKILL)
