import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from identity.deletion_ledger import read_deletions
from identity.models import Organization, Scan, User


class Command(BaseCommand):
    help = 'Valida todo o registro e reaplica exclusões antes de reabrir uma restauração offline.'

    def add_arguments(self, parser):
        parser.add_argument('--ledger', required=True)
        parser.add_argument('--expected-sha256', required=True)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--validate-only', action='store_true')

    def handle(self, *args, **options):
        try:
            records = read_deletions(options['ledger'], options['expected_sha256'])
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise CommandError('Registro/checkpoint inválido ou indisponível; restauração não pode reabrir.') from error
        targets = {kind: set() for kind in ('scan', 'organization', 'user')}
        for record in records:
            targets[record['kind']].add(record['target'])
        if options['validate_only']:
            self.stdout.write(json.dumps({'validated': True, 'intents': len(records)}))
            return
        counts = {}
        # Offline only: API and consumers must remain stopped until commit.
        with transaction.atomic():
            for kind, model in [('organization', Organization), ('user', User), ('scan', Scan)]:
                ids = sorted(targets[kind])
                counts[kind] = 0
                for start in range(0, len(ids), 500):
                    query = model.objects.filter(id__in=ids[start:start + 500])
                    counts[kind] += query.count()
                    if options['apply']:
                        query.delete()
        self.stdout.write(json.dumps({'dryRun': not options['apply'], 'matched': counts, 'intents': len(records)}))
