from datetime import timedelta
from unittest.mock import patch
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from identity.models import AbuseBucket, Scan, Site
from identity.services import create_user_workspace


class AbuseTests(APITestCase):
    def setUp(self):
        self.user, self.org = create_user_workspace(email='limits@example.com', password='Strong-pass-2026!', display_name='Limits', account_type='platform_developer')
        self.site = Site.objects.create(organization=self.org, display_name='Site', normalized_url='https://example.com/')
        self.client.force_authenticate(self.user)
        self.url = reverse('request-scan', args=[self.site.id])

    def request_scan(self, index=0, **headers):
        return self.client.post(self.url, {}, format='json', HTTP_IDEMPOTENCY_KEY=f'abuse-request-{index:016d}', **headers)

    @override_settings(SCAN_RATE_LIMITS={'user': 1, 'organization': 20, 'domain': 20, 'ip': 20})
    def test_user_limit_is_429_with_retry_after_and_idempotent_replay_is_free(self):
        first = self.request_scan()
        self.assertEqual(first.status_code, 202)
        self.assertEqual(self.request_scan().data['id'], first.data['id'])
        with self.assertLogs('identity.abuse', level='WARNING') as logs:
            denied = self.request_scan(1)
        self.assertEqual(denied.status_code, 429)
        self.assertGreater(int(denied['Retry-After']), 0)
        self.assertEqual(denied.data['code'], 'RATE_LIMITED')
        self.assertNotIn('limits@example.com', str(logs.output))
        self.assertEqual(Scan.objects.count(), 1)
        self.assertEqual(AbuseBucket.objects.get(scope='scan_user').denied, 1)

    def test_each_scan_scope_is_enforced_and_rejected_work_is_not_queued(self):
        for scope in ('organization', 'domain', 'ip'):
            with self.subTest(scope=scope):
                Scan.objects.all().delete()
                AbuseBucket.objects.all().delete()
                limits = dict(user=20, organization=20, domain=20, ip=20)
                limits[scope] = 1
                with override_settings(SCAN_RATE_LIMITS=limits):
                    self.assertEqual(self.request_scan().status_code, 202)
                    self.assertEqual(self.request_scan(1).status_code, 429)
                    self.assertEqual(Scan.objects.count(), 1)

    @override_settings(SCAN_ACTIVE_ORGANIZATION_LIMIT=1)
    def test_queue_capacity_includes_pending_jobs_and_retry_cannot_bypass_it(self):
        self.assertEqual(self.request_scan().status_code, 202)
        self.assertEqual(self.request_scan(1).status_code, 429)
        failed = Scan.objects.create(organization=self.org, site=self.site, idempotency_key='failed-attempt-0001', status='failed', attempts=1)
        self.assertEqual(self.client.post(reverse('scan-action', args=[failed.id]), {'action': 'retry'}, format='json').status_code, 429)
        failed.refresh_from_db()
        self.assertEqual(failed.status, 'failed')
        Scan.objects.exclude(id=failed.id).update(status='cancelled')
        self.assertEqual(self.client.post(reverse('scan-action', args=[failed.id]), {'action': 'retry'}, format='json').status_code, 200)

    @override_settings(SCAN_ACTIVE_GLOBAL_LIMIT=1)
    def test_global_capacity_and_cancellation(self):
        self.assertEqual(self.request_scan().status_code, 202)
        scan = Scan.objects.get()
        self.assertEqual(self.request_scan(1).status_code, 429)
        self.assertEqual(self.client.post(reverse('scan-action', args=[scan.id]), {'action': 'cancel'}, format='json').status_code, 200)
        self.assertEqual(self.request_scan(1).status_code, 202)

    @override_settings(SCAN_RATE_LIMITS={'user': 1, 'organization': 20, 'domain': 20, 'ip': 20})
    def test_budget_resets_after_window(self):
        self.assertEqual(self.request_scan().status_code, 202)
        with patch('identity.abuse.timezone.now', return_value=timezone.now() + timedelta(hours=2)):
            self.assertEqual(self.request_scan(1).status_code, 202)

    @override_settings(AUTH_RATE_LIMITS={'login': (1, 60), 'register': (1, 3600), 'demo': (1, 60)})
    def test_invalid_logins_and_registration_attempts_are_limited_before_validation(self):
        self.client.force_authenticate(None)
        for route in ('login', 'register', 'demo-login'):
            self.assertNotEqual(self.client.post(reverse(route), {}, format='json').status_code, 429)
            response = self.client.post(reverse(route), {}, format='json', HTTP_X_FORWARDED_FOR='8.8.8.8', HTTP_X_OMNISIGHT_CLIENT_IP='9.9.9.9')
            self.assertEqual(response.status_code, 429)
            self.assertIn('Retry-After', response)

    def test_ip_identity_ignores_untrusted_headers_and_stores_no_raw_identifier(self):
        from identity.abuse import client_ip
        from rest_framework.test import APIRequestFactory
        request = APIRequestFactory().get('/', REMOTE_ADDR='127.0.0.1', HTTP_X_OMNISIGHT_CLIENT_IP='8.8.8.8')
        self.assertEqual(client_ip(request), '127.0.0.1')
        with override_settings(TRUST_PROXY_CLIENT_IP=True):
            self.assertEqual(client_ip(request), '8.8.8.8')
        self.request_scan()
        self.assertFalse(AbuseBucket.objects.filter(key__contains='127.0.0.1').exists())
        self.assertFalse(AbuseBucket.objects.filter(key__contains='example.com').exists())

    def test_domain_budget_is_shared_across_tenants_and_subpaths(self):
        with override_settings(SCAN_RATE_LIMITS={'user': 20, 'organization': 20, 'domain': 1, 'ip': 20}):
            self.assertEqual(self.request_scan().status_code, 202)
            other, org = create_user_workspace(email='other-limit@example.com', password='Strong-pass-2026!', display_name='Other', account_type='platform_developer')
            self.site = Site.objects.create(organization=org, display_name='Other', normalized_url='https://example.com/other')
            self.url = reverse('request-scan', args=[self.site.id])
            self.client.force_authenticate(other)
            self.assertEqual(self.request_scan(1).status_code, 429)
            self.assertFalse(Scan.objects.filter(organization=org).exists())

    def test_metrics_alerts_without_disclosing_bucket_identities(self):
        import io, json
        from django.core.management import call_command, CommandError
        self.request_scan()
        output = io.StringIO()
        call_command('abuse_metrics', stdout=output)
        self.assertFalse(json.loads(output.getvalue())['alert'])
        AbuseBucket.objects.filter(scope='scan_ip').update(denied=5)
        output = io.StringIO()
        with self.assertRaises(CommandError):
            call_command('abuse_metrics', stdout=output)
        result = json.loads(output.getvalue())
        self.assertTrue(result['alert'])
        self.assertNotIn('key', output.getvalue())
        self.assertNotIn('example.com', output.getvalue())

    @override_settings(SCAN_RATE_LIMITS={'user': 1, 'organization': 20, 'domain': 20, 'ip': 20})
    def test_rejected_request_does_not_debit_other_budgets(self):
        self.request_scan()
        self.request_scan(1)
        self.assertEqual(AbuseBucket.objects.get(scope='scan_domain').count, 1)
        self.assertEqual(AbuseBucket.objects.get(scope='scan_ip').count, 1)

    def test_viewer_denial_does_not_consume_scan_budget(self):
        from identity.models import Membership
        Membership.objects.filter(user=self.user).update(role='viewer')
        self.assertEqual(self.request_scan().status_code, 403)
        self.assertFalse(AbuseBucket.objects.filter(scope__startswith='scan_').exists())

    def test_api_budget_limits_polling_and_health_remains_available(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        AbuseBucket.objects.filter(scope='api_ip').update(count=120)
        self.assertEqual(self.client.get(self.url).status_code, 429)
        self.assertEqual(self.client.get(reverse('health')).status_code, 200)

    def test_site_budget_rejects_before_dns_resolution(self):
        self.client.get(self.url)
        from identity.abuse import bucket
        from django.db import transaction
        with transaction.atomic():
            row = bucket('site_user', self.user.pk, 3600)
            row.count = 20
            row.save()
        with patch('identity.views.resolve_public_destination') as resolve:
            self.assertEqual(self.client.post(reverse('sites'), {'displayName': 'Extra', 'url': 'https://example.net/'}, format='json').status_code, 429)
            resolve.assert_not_called()
