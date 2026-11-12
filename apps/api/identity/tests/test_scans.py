from django.urls import reverse
from rest_framework.test import APITestCase
from identity.models import Site, Scan
from identity.services import create_user_workspace
from identity.scans import transition_scan

class ScanTests(APITestCase):
    def setUp(self):
        self.user, self.org = create_user_workspace(email='scan@example.com', password='Strong-pass-2026!', display_name='Scan', account_type='platform_developer')
        self.site = Site.objects.create(organization=self.org, display_name='Site', normalized_url='https://example.com/')
        self.client.force_authenticate(self.user)
        self.url = reverse('request-scan', args=[self.site.id])
        self.key = 'request-key-000001'

    def request(self, key=None, payload=None):
        return self.client.post(self.url, payload or {}, format='json', HTTP_IDEMPOTENCY_KEY=key or self.key)

    def test_repeating_request_returns_same_persisted_scan(self):
        first = self.request()
        second = self.request(payload={'viewport':'desktop'})
        self.assertEqual(first.status_code, 202)
        self.assertEqual(first.data['id'], second.data['id'])
        self.assertEqual(first.data['status'], 'queued')
        self.assertEqual(Scan.objects.count(), 1)

    def test_key_cannot_be_reused_for_another_site(self):
        self.request()
        other = Site.objects.create(organization=self.org, display_name='Other', normalized_url='https://other.example/')
        self.url = reverse('request-scan', args=[other.id])
        self.assertEqual(self.request().status_code, 409)

    def test_other_organization_cannot_read_or_request_scan(self):
        scan = self.request().data['id']
        other, _ = create_user_workspace(email='other-scan@example.com', password='Strong-pass-2026!', display_name='Other', account_type='platform_developer')
        self.client.force_authenticate(other)
        self.assertEqual(self.request().status_code, 404)
        self.assertEqual(self.client.get(reverse('scan-detail',args=[scan])).status_code, 404)

    def test_requires_key_and_rejects_unknown_options(self):
        self.assertEqual(self.client.post(self.url,{},format='json').status_code,400)
        self.assertEqual(self.request(key='short').status_code,400)
        self.assertEqual(self.request(payload={'depth':999}).status_code,400)
        self.assertEqual(Scan.objects.count(),0)

    def test_transitions_are_atomic_and_retry_is_bounded(self):
        scan_id = self.request().data['id']
        for _ in range(3):
            transition_scan(scan_id, 'running')
            with self.assertRaises(ValueError):
                transition_scan(scan_id, 'running')
            transition_scan(scan_id, 'failed')
            if Scan.objects.get(id=scan_id).attempts < 3:
                transition_scan(scan_id, 'queued')
        with self.assertRaises(ValueError):
            transition_scan(scan_id,'queued')
        self.assertEqual(Scan.objects.get(id=scan_id).attempts,3)

    def test_cancelled_and_completed_scans_are_terminal(self):
        scan_id = self.request().data['id']
        transition_scan(scan_id,'cancelled')
        with self.assertRaises(ValueError):
            transition_scan(scan_id,'running')
        scan_id = self.request(key='request-key-000002').data['id']
        transition_scan(scan_id,'running')
        transition_scan(scan_id,'completed')
        scan = Scan.objects.get(id=scan_id)
        self.assertIsNotNone(scan.started_at)
        self.assertIsNotNone(scan.completed_at)
        with self.assertRaises(ValueError):
            transition_scan(scan_id,'queued')
