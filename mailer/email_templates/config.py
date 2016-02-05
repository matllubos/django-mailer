from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    MAILER_DEFAULT_FROM_EMAIL = settings.MAILER_DEFAULT_FROM_EMAIL
except:
    raise ImproperlyConfigured('email_templates needs EMAIL_DEFAULT_FROM_EMAIL set in settings.py')

try:
    MAILER_DEFAULT_PRIORITY = settings.MAILER_DEFAULT_PRIORITY
except:
    raise ImproperlyConfigured('email_templates needs EMAIL_DEFAULT_PRIORITY set in settings.py')


def get_email_template_model():
    from django.db.models import get_model

    try:
        app_label, model_name = settings.MAILER_TEMPLATE_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured('email_templates needs MAILER_TEMPLATE_MODEL set in settings.py as'
                                   ' app_label.model_name')

    template_model = get_model(app_label, model_name)
    if template_model is None:
        raise ImproperlyConfigured('MAILER_TEMPLATE_MODEL refers to model \'%s\' '
                                   'that has not been installed' % settings.MAILER_TEMPLATE_MODEL)
    return template_model