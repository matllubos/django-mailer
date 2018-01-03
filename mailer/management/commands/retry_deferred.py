import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import connection

from mailer.models import Message


class Command(BaseCommand):
    help = "Attempt to resend any deferred mail."

    def add_arguments(self, parser):
        parser.add_argument('-c', '--cron', dest='cron', action='store_true', default=False,
                            help='If 1 don\'t print messagges, but only errors.')

    def handle(self, cron, **options):
        if not cron:
            logging.basicConfig(level=logging.DEBUG, format="%(message)s")
        else:
            logging.basicConfig(stream=self.stderr, level=logging.ERROR, format="%(message)s")
        count = Message.objects.retry_deferred()
        logging.info("%s message(s) retried" % count)
        connection.close()
