import logging
import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from identity.privacy import purge_expired

logger = logging.getLogger('identity.privacy')


class Command(BaseCommand):
    help = 'Descarta lotes expirados a cada minuto; usa a política configurada no servidor.'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')

    def handle(self, *args, **options):
        while True:
            close_old_connections()
            result = purge_expired()
            # Counts only; never record identities or report content.
            logger.warning('retention_sweep scans_deleted=%s buckets_deleted=%s', result['scansDeleted'], result['bucketsDeleted'])
            if options['once']:
                return
            time.sleep(60)
