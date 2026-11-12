"""CI-only fixtures for encrypted dump -> account closure -> restore -> deletion replay."""
import os
from django.conf import settings
from identity.models import User, ScanReport, Site, Scan
from identity.services import create_user_workspace
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

phase = os.environ.get('RESTORE_DRILL_PHASE')
database = settings.DATABASES['default']['NAME']
expected = 'omnisight_restore_ci' if phase == 'verify' else 'omnisight_backup_ci'
if os.environ.get('CI') != 'true' or database != expected:
    raise RuntimeError('Restore drill is restricted to disposable CI databases.')
password = 'CI-only-recovery-password-2026!'
if phase == 'seed':
    user, org = create_user_workspace(email='delete-drill@example.com', password=password, display_name='Delete drill', account_type='platform_developer')
    site = Site.objects.create(organization=org, normalized_url='https://example.com/', display_name='Fixture')
    scan = Scan.objects.create(organization=org, site=site, idempotency_key='restore-drill-key-0001', status='completed')
    ScanReport.objects.create(scan=scan, engine_version='4.13.0', payload={'pages': []})
    survivor, _ = create_user_workspace(email='keep-drill@example.com', password=password, display_name='Keep drill', account_type='platform_developer')
    Token.objects.create(user=survivor)
elif phase == 'close':
    client = APIClient(); client.force_authenticate(User.objects.get(email='delete-drill@example.com'))
    response = client.post('/api/auth/account/close/', {'password': password, 'confirmation': 'ENCERRAR MINHA CONTA'}, format='json')
    if response.status_code != 204:
        raise RuntimeError('Fixture closure failed.')
elif phase == 'verify':
    if User.objects.filter(email='delete-drill@example.com').exists() or ScanReport.objects.exists():
        raise RuntimeError('Deleted fixture was resurrected.')
    if not User.objects.filter(email='keep-drill@example.com').exists() or Token.objects.exists():
        raise RuntimeError('Survivor missing or restored tokens not revoked.')
    print('RESTORE_DRILL_OK: retained user preserved, deleted account/report absent, tokens revoked.')
else:
    raise RuntimeError('Unknown fixture phase.')
