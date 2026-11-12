"""Durable DB queue with bounded attempts and expiring, fenced ownership."""
from datetime import timedelta
import json
import logging
import os
import uuid
import subprocess
import sys
import signal
from pathlib import Path
from urllib.error import HTTPError, URLError

from django.db import transaction
from django.utils import timezone
from identity.models import Scan, ScanReport
from identity.pipeline import validate_analysis

logger = logging.getLogger(__name__)
LEASE_SECONDS = 180
MAX_ATTEMPTS = 3
MAX_REPORT_BYTES = 1024 * 1024


def recover_expired():
    now = timezone.now()
    expired = Scan.objects.filter(status='running', lease_expires_at__lte=now)
    expired.filter(attempts__lt=MAX_ATTEMPTS).update(status='queued',lease_token=None,lease_expires_at=None,started_at=None,completed_at=None,error_code='')
    expired.filter(attempts__gte=MAX_ATTEMPTS).update(status='failed',lease_token=None,lease_expires_at=None,completed_at=now,error_code='WORKER_EXPIRED')


def claim_scan():
    recover_expired()
    # CAS is effective on SQLite and PostgreSQL; no SELECT lock dependency.
    for candidate in Scan.objects.filter(status='queued',attempts__lt=MAX_ATTEMPTS,site__deleted_at__isnull=True).order_by('requested_at')[:20]:
        now = timezone.now()
        changed = Scan.objects.filter(id=candidate.id,status='queued',attempts=candidate.attempts).update(status='running',attempts=candidate.attempts+1,started_at=now,completed_at=None,lease_token=uuid.uuid4(),lease_expires_at=now+timedelta(seconds=LEASE_SECONDS),error_code='')
        if changed:
            claimed = Scan.objects.select_related('site').filter(id=candidate.id, status='running').first()
            if claimed:
                return claimed
    return None


def owned(scan):
    return Scan.objects.filter(id=scan.id,status='running',lease_token=scan.lease_token,lease_expires_at__gt=timezone.now())


def publish_report(scan,payload):
    if len(json.dumps(payload).encode()) > MAX_REPORT_BYTES:
        raise ValueError('Relatório excede o limite de armazenamento.')
    with transaction.atomic():
        if not owned(scan).update(status='completed',completed_at=timezone.now(),lease_token=None,lease_expires_at=None,error_code=''):
            raise ValueError('A execução perdeu sua concessão de trabalho.')
        ScanReport.objects.create(scan=scan,engine_version=payload['engineVersion'],payload=payload)


def collect_and_analyze(url):
    # A process deadline covers DNS as well as HTTP and browser execution.
    env={key:os.environ[key] for key in ['PATH','HOME','TMPDIR','BROWSER_SERVICE_URL'] if key in os.environ}
    process=subprocess.Popen([sys.executable,'-m','identity.pipeline'],cwd=Path(__file__).resolve().parents[1],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env,start_new_session=True)
    try:
        raw,_=process.communicate(json.dumps({'url':url}).encode(),timeout=90)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.communicate()
        raise TimeoutError('O pipeline excedeu o orçamento de execução.')
    if process.returncode or len(raw)>MAX_REPORT_BYTES:
        raise ValueError('O pipeline não concluiu a análise.')
    payload=json.loads(raw)
    if not isinstance(payload,dict) or payload.get('schemaVersion')!=1 or payload.get('engineVersion')!='4.13.0' or payload.get('mode')!='offline-html' or not isinstance(payload.get('pages'),list) or len(payload['pages'])!=1:
        raise ValueError('Snapshot de análise incompatível.')
    for page in payload['pages']:
        validate_analysis(page)
    return payload


def process_next():
    scan=claim_scan()
    if scan is None:
        return False
    try:
        report=collect_and_analyze(scan.site.normalized_url)
        publish_report(scan,report)
    except (TimeoutError,HTTPError,URLError,ValueError,OSError) as error:
        code='SCAN_TIMEOUT' if isinstance(error,TimeoutError) else 'SCAN_EXECUTION_FAILED'
        owned(scan).update(status='failed',completed_at=timezone.now(),lease_token=None,lease_expires_at=None,error_code=code)
        # Never log URL, HTML, credentials or raw upstream exception messages.
        logger.warning('scan_failed id=%s correlation=%s code=%s',scan.id,scan.correlation_id,code)
    return True
