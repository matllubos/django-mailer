import time
import smtplib
import logging

from mailer.lockfile import FileLock, AlreadyLocked, LockTimeout
from socket import error as socket_error

from django.conf import settings
from django.core.mail import send_mail as core_send_mail
from django.core.mail import get_connection

from mailer.models import Message


# when queue is empty, how long to wait (in seconds) before checking again
EMPTY_QUEUE_SLEEP = getattr(settings, "MAILER_EMPTY_QUEUE_SLEEP", 30)

# lock timeout value. how long to wait for the lock to become available.
# default behavior is to never wait for the lock to be available.
LOCK_WAIT_TIMEOUT = getattr(settings, "MAILER_LOCK_WAIT_TIMEOUT", -1)

EMAIL_LOCK_FILE = getattr(settings, "MAILER_LOCK_FILE", "mailer_send_mail")

#maximum mails count wich could be send per one 'send_all' execution
MAXIMUM_MAILS_PER_COMMAND = getattr(settings, "MAILER_MAXIMUM_EMAILS_PER_COMMAND", -1)


def prioritize(max_mails):
    """
    Return the messages in the queue in the order they should be sent.
    """
    qs = Message.objects.pending()
    if max_mails > 0:
        return qs[:max_mails]
    return qs

def send_all():
    """
    Send all eligible messages in the queue.
    """
    # The actual backend to use for sending, defaulting to the Django default.
    # To make testing easier this is not stored at module level.
    EMAIL_BACKEND = getattr(settings, "MAILER_EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    
    lock = FileLock(EMAIL_LOCK_FILE)
    
    logging.debug("acquiring lock...")
    try:
        lock.acquire(LOCK_WAIT_TIMEOUT)
    except AlreadyLocked:
        logging.debug("lock already in place. quitting.")
        return
    except LockTimeout:
        logging.debug("waiting for the lock timed out. quitting.")
        return
    logging.debug("acquired.")
    
    start_time = time.time()

    deferred = 0
    sent = 0
    
    try:
        connection = None
        for message in prioritize(MAXIMUM_MAILS_PER_COMMAND):
            try:
                if connection is None:
                    connection = get_connection(backend=EMAIL_BACKEND)
                logging.info("sending message [%s] '%s' to %s" % (message.id, message.subject, message.recipients))
                email = message.email
                email.connection = connection
                if not hasattr(email, 'reply_to'):
                    # Compatability fix for EmailMessage objects
                    # pickled when running < Django 1.8 and then
                    # unpickled under Django 1.8
                    email.reply_to = []
                email.send()
                message.set_sent()
                sent += 1
            except (socket_error, smtplib.SMTPSenderRefused, smtplib.SMTPRecipientsRefused,
                    smtplib.SMTPAuthenticationError) as err:
                message.defer()
                logging.info("message deferred due to failure: %s" % err)
                deferred += 1
                # Get new connection, it case the connection itself has an error.
                connection = None
    finally:
        logging.debug("releasing lock...")
        lock.release()
        logging.debug("released.")
    
    logging.info("")
    logging.info("%s sent; %s deferred;" % (sent, deferred))
    logging.info("done in %.2f seconds" % (time.time() - start_time))


def send_loop():
    """
    Loop indefinitely, checking queue at intervals of EMPTY_QUEUE_SLEEP and
    sending messages if any are on queue.
    """
    
    while True:
        while not Message.objects.all():
            logging.debug("sleeping for %s seconds before checking queue again" % EMPTY_QUEUE_SLEEP)
            time.sleep(EMPTY_QUEUE_SLEEP)
        send_all()
