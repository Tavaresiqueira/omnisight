import json
from django.core.management.base import BaseCommand, CommandError
from identity.privacy import purge_expired


class Command(BaseCommand):
    help = 'Conta dados expirados; --apply executa exclusão em lote limitado.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--batch-size', type=int, default=100)

    def handle(self, *args, **options):
        try:
            result = purge_expired(batch_size=options['batch_size'], dry_run=not options['apply'])
        except ValueError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result))
