"""Bounded disposal of terminal scans and expired pseudonymous rate identities."""
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from identity.models import AbuseBucket, Scan


def purge_expired(*, batch_size=100, dry_run=False):
    if type(batch_size) is not int or not 1 <= batch_size <= 1000:
        raise ValueError('O lote deve conter entre 1 e 1000 registros por categoria.')
    now = timezone.now()
    cutoff = now - timedelta(days=settings.SCAN_RETENTION_DAYS)
    scans = Scan.objects.filter(status__in=['completed', 'failed', 'cancelled']).filter(
        Q(completed_at__lt=cutoff) | Q(completed_at__isnull=True, requested_at__lt=cutoff)
    )
    buckets = AbuseBucket.objects.exclude(scope='scan_capacity').filter(resets_at__lt=now - timedelta(days=settings.ABUSE_RETENTION_DAYS))
    if dry_run:
        return {'dryRun': True, 'scansEligible': scans.count(), 'bucketsEligible': buckets.count()}
    # skip_locked avoids waiting for a worker publishing or API consuming a budget.
    # SQLite does not implement row locks; concurrent production requires PostgreSQL.
    with transaction.atomic():
        ids = list(scans.select_for_update(skip_locked=True).order_by('id').values_list('id', flat=True)[:batch_size])
        Scan.objects.filter(id__in=ids).delete()  # Cascades to all report evidence/screenshots.
    with transaction.atomic():
        bucket_ids = list(buckets.select_for_update(skip_locked=True).order_by('id').values_list('id', flat=True)[:batch_size])
        AbuseBucket.objects.filter(id__in=bucket_ids).delete()
    return {'dryRun': False, 'scansDeleted': len(ids), 'bucketsDeleted': len(bucket_ids)}


class PrivateApiCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/api/') and request.path != '/api/health/':
            response['Cache-Control'] = 'no-store, private'
        return response
