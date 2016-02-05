from __future__ import unicode_literals

from django.template import Context, Template
from django.db.models.loading import get_model

from mailer import send_html_mail
from mailer.email_templates.models import EmailTemplate
from mailer.email_templates import config


class EmailTemplateSender(object):
    default_context_data = {}
    default_from_email = config.MAILER_DEFAULT_FROM_EMAIL
    default_priority = config.MAILER_DEFAULT_PRIORITY
    default_auth_user = None
    default_auth_password = None
    default_headers = {}
    default_fail_silently = False
    default_message = ' '
    default_content_object = None
    default_tag = None

    def send_html_mail_from_email_template(self, template_name, recipient_list, attachments=None,
                                           cached_template_obj=None, **kwargs):

        for attr_name in ('context_data', 'from_email', 'priority', 'fail_silently', 'auth_user',
                          'auth_password', 'headers', 'message', 'content_object', 'tag'):
            kwargs[attr_name] = kwargs.get(attr_name, getattr(self, 'default_%s' % attr_name))

        context = Context(kwargs['context_data'])
        email_template = self.get_email_template_object(template_name, cached_template_obj)

        subject_template = self.subject_before_render(email_template)
        subject = Template(subject_template).render(context).encode('utf-8')
        subject = self.subject_after_render(subject)

        html_template = self.before_render(email_template)
        html_message = Template(html_template).render(context).encode('utf-8')
        html_message = self.after_render(html_message)

        kwargs['subject'] = subject
        kwargs['message_html'] = html_message
        kwargs['recipient_list'] = recipient_list
        kwargs['attachments'] = attachments
        kwargs['template_slug'] = template_name

        del kwargs['context_data']

        self.before_sent(**kwargs)
        send_html_mail(**kwargs)
        self.after_sent(**kwargs)
        return True

    def before_render(self, email_template):
        return email_template.html_body

    def after_render(self, html):
        return html

    def before_sent(self, **kwargs):
        pass

    def after_sent(self, **kwargs):
        pass

    def subject_before_render(self, email_template):
        return email_template.subject

    def subject_after_render(self, subject):
        return subject

    def get_rendered_email_template(self, template_name=None, template_obj=None, context_data={}):
        context = Context(context_data)
        email_template = self.get_email_template_object(template_name, template_obj)
        html_template = email_template.html_body
        return self.after_render(Template(html_template).render(context).encode('utf-8'))

    def get_email_template_class(self):
        return config.get_email_template_model()

    def get_email_template_object(self, template_name=None, template_obj=None):
        model = self.get_email_template_class()
        if isinstance(template_obj, model):
            return template_obj
        else:
            return model.objects.get(slug=template_name)

template_sender = EmailTemplateSender()
