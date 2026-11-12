from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APITestCase
from identity.models import Scan, Site
from identity.services import create_user_workspace
from identity.worker import claim_scan,publish_report

class ScanApiTests(APITestCase):
    def setUp(self):
        self.user,self.org=create_user_workspace(email='report@example.com',password='Strong-pass-2026!',display_name='Report',account_type='platform_developer')
        self.site=Site.objects.create(organization=self.org,display_name='Site',normalized_url='https://example.com/')
        self.scan=Scan.objects.create(organization=self.org,site=self.site,idempotency_key='api-key-0000000001')
        self.client.force_authenticate(self.user)

    def test_completed_report_is_readable_only_by_its_organization(self):
        publish_report(claim_scan(),{'engine':'axe-core','engineVersion':'4.13.0','pages':[]})
        url=reverse('scan-report',args=[self.scan.id]);self.assertEqual(self.client.get(url).status_code,200)
        other,_=create_user_workspace(email='foreign@example.com',password='Strong-pass-2026!',display_name='Other',account_type='platform_developer')
        self.client.force_authenticate(other);self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.get(reverse('request-scan',args=[self.site.id])).status_code,404)

    def test_cancel_prevents_worker_publication_and_retry_is_bounded(self):
        claimed=claim_scan();url=reverse('scan-action',args=[self.scan.id])
        self.assertEqual(self.client.post(url,{'action':'cancel'},format='json').status_code,200)
        with self.assertRaises(ValueError):publish_report(claimed,{'engineVersion':'4.13.0'})
        self.assertEqual(self.client.post(url,{'action':'retry'},format='json').status_code,409)

    def test_failed_job_can_be_requeued_without_creating_a_duplicate(self):
        Scan.objects.filter(id=self.scan.id).update(status='failed',attempts=1,error_code='SCAN_TIMEOUT')
        url=reverse('scan-action',args=[self.scan.id])
        r=self.client.post(url,{'action':'retry'},format='json');self.assertEqual(r.status_code,200);self.assertEqual(r.data['status'],'queued')
        self.assertEqual(Scan.objects.count(),1)
        Scan.objects.filter(id=self.scan.id).update(status='failed',attempts=3)
        self.assertEqual(self.client.post(url,{'action':'retry'},format='json').status_code,409)

    def test_list_and_error_codes_do_not_expose_source_or_lease(self):
        r=self.client.get(reverse('request-scan',args=[self.site.id]));self.assertEqual(r.status_code,200);self.assertEqual(len(r.data['items']),1)
        self.assertNotIn('lease_token',r.data['items'][0]);self.assertIn('errorCode',r.data['items'][0])

    def test_viewer_can_read_but_cannot_request_or_change_scans(self):
        from identity.models import Membership
        Membership.objects.filter(user=self.user,organization=self.org).update(role='viewer')
        self.assertEqual(self.client.get(reverse('request-scan',args=[self.site.id])).status_code,200)
        self.assertEqual(self.client.post(reverse('request-scan',args=[self.site.id]),{},format='json',HTTP_IDEMPOTENCY_KEY='viewer-attempt-0001').status_code,403)
        self.assertEqual(self.client.post(reverse('scan-action',args=[self.scan.id]),{'action':'cancel'},format='json').status_code,403)

    def test_health_is_public_and_checks_database(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(reverse('health')).data,{'status':'ok'})
