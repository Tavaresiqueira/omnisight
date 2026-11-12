import json
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum
from django.utils import timezone
from identity.models import AbuseBucket, Scan


class Command(BaseCommand):
    help = 'Resumo agregado das janelas ativas; saída não contém IP, URL ou usuário.'

    def add_arguments(self, parser):
        parser.add_argument('--alert-threshold', type=int, default=5)

    def handle(self, *args, **options):
        threshold = options['alert_threshold']
        if threshold < 1:
            raise CommandError('O limiar deve ser positivo.')
        scopes = list(AbuseBucket.objects.filter(resets_at__gt=timezone.now()).values('scope').annotate(accepted=Sum('count'), denied=Sum('denied')).order_by('scope'))
        alert = any(row['denied'] >= threshold for row in scopes)
        self.stdout.write(json.dumps({'scopes': scopes, 'activeScans': Scan.objects.filter(status__in=['queued', 'running']).count(), 'alert': alert}))
        if alert:
            raise CommandError('ABUSE_ALERT: limiar de bloqueios atingido.')
