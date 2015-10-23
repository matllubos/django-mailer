from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from easymode.i18n.decorators import I18n


@I18n('subject', 'html_body')
class AbstractEmailTemplate(models.Model):
    slug = models.SlugField(max_length=100, null=False, blank=False, primary_key=True, verbose_name=_('Slug'))
    subject = models.CharField(max_length=100, null=True, blank=False, verbose_name=_('Subject'))
    html_body = models.TextField(null=True, blank=False, verbose_name=_('HTML body'))

    class Meta:
        abstract = True
        verbose_name = _('E-mail')
        verbose_name_plural = _('E-mails')
