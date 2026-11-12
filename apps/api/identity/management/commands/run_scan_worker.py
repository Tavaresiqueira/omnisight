import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from identity.worker import process_next

class Command(BaseCommand):
    help='Consome scans persistidos; uma execução por processo.'
    def add_arguments(self,parser):
        parser.add_argument('--once',action='store_true')
    def handle(self,*args,**options):
        while True:
            close_old_connections()
            worked=process_next()
            if options['once']:
                return
            if not worked:
                time.sleep(2)
