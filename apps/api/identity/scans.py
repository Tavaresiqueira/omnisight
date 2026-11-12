from django.utils import timezone
from identity.models import Scan


def transition_scan(scan_id, target):
    """Compare-and-swap prevents two workers from claiming the same queued job."""
    scan = Scan.objects.get(id=scan_id)
    allowed = {
        'queued': {'running', 'cancelled'},
        'running': {'completed', 'failed', 'cancelled'},
        'failed': {'queued'},
    }
    if target not in allowed.get(scan.status, set()):
        raise ValueError('Transição de scan inválida.')
    if target == 'queued' and scan.attempts >= 3:
        raise ValueError('Limite de três tentativas atingido.')
    changes = {'status': target, 'lease_token': None, 'lease_expires_at': None, 'error_code': ''}
    if target == 'running':
        changes.update(attempts=scan.attempts + 1, started_at=timezone.now(), completed_at=None)
    elif target in {'completed', 'failed', 'cancelled'}:
        changes['completed_at'] = timezone.now()
    elif target == 'queued':
        changes.update(started_at=None, completed_at=None)
    changed = Scan.objects.filter(id=scan_id, status=scan.status, attempts=scan.attempts).update(**changes)
    if not changed:
        raise ValueError('O estado do scan foi alterado por outra execução.')
    return Scan.objects.get(id=scan_id)
