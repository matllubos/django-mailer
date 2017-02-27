import logging
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from mailer.engine import send_all


# allow a sysadmin to pause the sending of mail temporarily.
PAUSE_SEND = getattr(settings, "MAILER_PAUSE_SEND", False)


class Command(BaseCommand):
    help = "Do one pass through the mail queue, attempting to send all mail."

    def add_arguments(self, parser):
        parser.add_argument('-c', '--cron', dest='cron', action='store_true', default=False,
                            help='If 1 don\'t print messagges, but only errors.')

    def handle(self, cron, **options):
        if not cron:
            logging.basicConfig(level=logging.DEBUG, format="%(message)s")
        else:
            logging.basicConfig(stream=self.stdout, level=logging.ERROR, format="%(message)s")
        logging.info("-" * 72)
        # if PAUSE_SEND is turned on don't do anything.
        if not PAUSE_SEND:
            send_all()
        else:
            logging.info("sending is paused, quitting.")
        connection.close()
