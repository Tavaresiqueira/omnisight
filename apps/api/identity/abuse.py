"""Shared fixed-window budgets. PostgreSQL row locks serialize admission across API processes."""
from datetime import timedelta
import ipaddress
import logging
import math
from urllib.parse import urlsplit

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework.exceptions import APIException, Throttled
from rest_framework.throttling import BaseThrottle
from identity.models import AbuseBucket, Scan
from identity.scans import transition_scan

logger = logging.getLogger(__name__)


class RateLimited(Throttled):
    def __init__(self, scope, wait):
        self.wait = max(1, math.ceil(wait))
        APIException.__init__(self, {
            'code': 'RATE_LIMITED',
            'message': 'Limite temporário atingido. Aguarde antes de tentar novamente.',
            'scope': scope,
        }, code='throttled')
        logger.warning('rate_limit_exceeded scope=%s retry_after=%s', scope, self.wait)


def client_ip(request):
    # Only enable behind the private API network and Caddy's overwritten header.
    value = request.META.get('REMOTE_ADDR', '')
    if settings.TRUST_PROXY_CLIENT_IP:
        value = request.META.get('HTTP_X_OMNISIGHT_CLIENT_IP', value)
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return 'unknown'


def bucket(scope, identity, seconds):
    key = salted_hmac('omnisight-abuse-' + scope, str(identity), algorithm='sha256').hexdigest()
    now = timezone.now()
    # A cleanup may remove an expired row while this transaction waits. Keeping
    # lookup/create on the locking queryset prevents a stale second lookup.
    row, _ = AbuseBucket.objects.select_for_update().get_or_create(scope=scope, key=key, defaults={'resets_at': now + timedelta(seconds=seconds)})
    if row.resets_at <= now:
        row.resets_at = now + timedelta(seconds=seconds)
        row.count = row.denied = 0
        row.save(update_fields=['resets_at', 'count', 'denied'])
    return row


def consume_locked(limits):
    """Caller owns transaction; denial commits before raising, with no partial budget debit."""
    rows = [(bucket(scope, identity, seconds), limit) for scope, identity, limit, seconds in sorted(limits)]
    for row, limit in rows:
        if row.count >= limit:
            row.denied += 1
            row.save(update_fields=['denied'])
            return RateLimited(row.scope, (row.resets_at - timezone.now()).total_seconds())
    for row, _ in rows:
        row.count += 1
        row.save(update_fields=['count'])
    return None


class ApiBudgetThrottle(BaseThrottle):
    def allow_request(self, request, view):
        ip = client_ip(request)
        limits = [('api_ip', ip, 120, 60)]
        scope = getattr(view, 'abuse_scope', None)
        if scope in settings.AUTH_RATE_LIMITS and (scope != 'closure' or request.method == 'POST'):
            limit, seconds = settings.AUTH_RATE_LIMITS[scope]
            limits.append(('auth_' + scope, ip, limit, seconds))
        if scope == 'closure' and request.method == 'POST':
            limits.append(('closure_user', request.user.pk, 5, 60))
        if scope == 'site' and request.method == 'POST':
            limits.append(('site_user', request.user.pk, 20, 3600))
        with transaction.atomic():
            denied = consume_locked(limits)
        if denied:
            raise denied
        return True


def enqueue_scan(user, site, key, ip, retry_id=None):
    # A single durable admission lock makes both queue counts and multi-scope
    # budgets atomic across organizations, including retries. No target fetch here.
    with transaction.atomic():
        capacity = bucket('scan_capacity', 'global', 60)
        existing = Scan.objects.filter(organization=site.organization, idempotency_key=key).first() if retry_id is None else None
        if existing:
            return existing
        if retry_id:
            scan = Scan.objects.select_for_update().filter(id=retry_id).first()
            if scan is None or scan.status != 'failed' or scan.attempts >= 3:
                raise ValueError('Este scan não pode ser executado novamente.')
        active = Scan.objects.filter(status__in=['queued', 'running'])
        denied = None
        if active.count() >= settings.SCAN_ACTIVE_GLOBAL_LIMIT or active.filter(organization=site.organization).count() >= settings.SCAN_ACTIVE_ORGANIZATION_LIMIT:
            capacity.denied += 1
            capacity.save(update_fields=['denied'])
            denied = RateLimited('scan_capacity', 30)
        else:
            values = {'user': user.pk, 'organization': site.organization_id, 'domain': urlsplit(site.normalized_url).hostname, 'ip': ip}
            denied = consume_locked([('scan_' + scope, identity, settings.SCAN_RATE_LIMITS[scope], 3600) for scope, identity in values.items()])
        if not denied:
            scan = transition_scan(retry_id, 'queued') if retry_id else Scan.objects.create(organization=site.organization, site=site, idempotency_key=key)
    if denied:
        raise denied
    return scan
