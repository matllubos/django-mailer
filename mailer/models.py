from __future__ import unicode_literals

import base64
import os
import pickle

from six import python_2_unicode_compatible

try:
    from django.utils.timezone import now as datetime_now
    datetime_now  # workaround for pyflakes
except ImportError:
    from datetime import datetime
    datetime_now = datetime.now

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.text import mark_safe
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html_join
from django.conf import settings
from django.core.files.base import ContentFile

try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.generic import GenericForeignKey


PRIORITY_HIGH = 1
PRIORITY_MEDIUM = 2
PRIORITY_LOW = 3

PRIORITY_CHOICES = (
    (PRIORITY_HIGH, _('High')),
    (PRIORITY_MEDIUM, _('Medium')),
    (PRIORITY_LOW, _('Low')),
)

PRIORITY_MAPPING = {
    'high': PRIORITY_HIGH,
    'medium': PRIORITY_MEDIUM,
    'low': PRIORITY_LOW,
}

STATUS_PENDING = 0
STATUS_SENT = 1
STATUS_DEFERRED = 2
STATUS_DEBUG = 3

STATUS_CHOICES = (
    (STATUS_PENDING, _('Pending')),
    (STATUS_SENT, _('Sent')),
    (STATUS_DEFERRED, _('Deferred')),
    (STATUS_DEBUG, _('Debug'))
)


class MessageManager(models.Manager):

    def pending(self):
        """
        the messages in the queue for sending
        """
        return self.filter(status=STATUS_PENDING).order_by('priority')

    def deferred(self):
        """
        the deferred messages in the queue
        """
        return self.filter(status=STATUS_DEFERRED)

    def retry_deferred(self):
        count = 0
        for message in self.deferred():
            if message.retry():
                count += 1
        return count

    def create_from_email_obj(self, subject, recipient_list, reply_to_list, from_email, email_obj, attachments, priority,
                              tag=None, template_slug=None, content_object=None):

        db_msg = Message(
            status=STATUS_PENDING if not getattr(settings, 'MAILER_DEBUG', False) else STATUS_DEBUG,
            priority=PRIORITY_MAPPING[priority],
            subject=subject,
            tag=tag,
            template_slug=template_slug,
            from_email=from_email
        )
        if content_object:
            db_msg.content_object = content_object
        db_msg.email = email_obj
        db_msg.set_recipients(recipient_list)
        db_msg.set_reply_to(reply_to_list)
        db_msg.save()
        for filename, content, _ in attachments or ():
            atachment = Attachment(message=db_msg)
            atachment.file.save(filename, ContentFile(content))
            atachment.save()
        return db_msg


def email_to_db(email):
    # pickle.dumps returns essentially binary data which we need to encode
    # to store in a unicode field.
    return base64.encodestring(pickle.dumps(email))


def db_to_email(data):
    if data == u"":
        return None
    else:
        try:
            return pickle.loads(base64.decodestring(data.encode('ascii')))
        except Exception:
            try:
                # previous method was to just do pickle.dumps(val)
                return pickle.loads(data.encode('ascii'))
            except Exception:
                return None


@python_2_unicode_compatible
class Message(models.Model):

    # The actual data - a pickled EmailMessage
    message_data = models.TextField()
    priority = models.PositiveSmallIntegerField(null=False, blank=False, choices=PRIORITY_CHOICES,
                                                default=PRIORITY_MEDIUM, verbose_name=_('priority'))
    status = models.PositiveIntegerField(null=False, blank=False, choices=STATUS_CHOICES, default=STATUS_PENDING,
                                         verbose_name=_('status'))
    created = models.DateTimeField(blank=False, null=False, default=datetime_now, verbose_name=_('created'))
    updated = models.DateTimeField(blank=False, null=False, auto_now=True, verbose_name=_('updated'))
    # Sender, recipients and subject are cached attrs (for list view)
    from_email = models.CharField(blank=True, null=True, max_length=200, verbose_name=_('from email'))
    recipients = models.TextField(blank=True, null=True, verbose_name=_('recipients'))
    reply_to = models.TextField(blank=True, null=True, verbose_name=_('reply to'))
    subject = models.TextField(blank=True, null=True, verbose_name=_('subject'))

    tag = models.SlugField(null=True, blank=True)
    template_slug = models.SlugField(verbose_name=_('template slug'), null=True, blank=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    objects = MessageManager()

    def defer(self):
        self.status = STATUS_DEFERRED
        self.save()

    def retry(self):
        if self.status == STATUS_DEFERRED:
            self.status = STATUS_PENDING
            self.save()
            return True
        else:
            return False

    def set_sent(self):
        self.status = STATUS_SENT
        self.save()

    def _get_email(self):
        return db_to_email(self.message_data)

    def _set_email(self, val):
        self.message_data = email_to_db(val)

    email = property(_get_email, _set_email)

    def set_recipients(self, recipients_list):
        self.recipients = ', '.join(recipients_list)

    def set_reply_to(self, reply_to_list):
        if reply_to_list:
            self.reply_to = ', '.join(reply_to_list)

    @property
    def to_addresses(self):
        email = self.email
        if email is not None:
            return email.to
        else:
            return []

    def get_email_content_for_admin_field(self):
        contents = []

        if self.email.body and self.email.body.strip():
            contents.append('<textarea cols="150" rows="20">%s</textarea>' % self.email.body)

        for alternative in self.email.alternatives:
            if alternative[1] == 'text/html':
                contents.append('<textarea cols="150" rows="20">%s</textarea>' % alternative[0])
            else:
                contents.append('<code>Alternative in mime type: %s</code>' % alternative[1])

        return mark_safe('<hr />'.join(contents))

    get_email_content_for_admin_field.short_description = _('e-mail content')

    def display_content_object(self, request):
        from is_core.utils import render_model_object_with_link

        return render_model_object_with_link(request, self.content_object) if self.content_object else None

    display_content_object.short_description = _('related object')

    def display_attachments(self, request):
        return format_html_join(', ', '<a href="{}">{}</a>', ((attachment.file.url, os.path.basename(attachment.file.name))
                                                              for attachment in self.attachments.all()))

    display_attachments.short_description = _('attachments')

    def __str__(self):
        return '#{}'.format(self.pk)

    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')


@python_2_unicode_compatible
class Attachment(models.Model):

    message = models.ForeignKey(Message, related_name='attachments')
    file = models.FileField(verbose_name=_('file'), null=False, blank=False, upload_to='mailer')

    def __str__(self):
        return '#{}'.format(self.pk)

    class Meta:
        verbose_name = _('attachment')
        verbose_name_plural = _('attachments')
