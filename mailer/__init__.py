VERSION = (2, 0, 3)


def get_version():
    return '.'.join(map(str, VERSION))

__version__ = get_version()


# replacement for django.core.mail.send_mail


def get_email_message_kwargs(subject, message, from_email, recipient_list, reply_to_list, attachments, headers):
    import django

    headers = headers or {}
    kwargs = {
        'subject': subject,
        'body': message,
        'from_email': from_email,
        'to': recipient_list,
        'attachments': attachments,
        'headers': headers,
    }
    if django.get_version() >= '1.8':
        kwargs['reply_to'] = reply_to_list
    elif reply_to_list:
        headers['Reply-To'] = ','.join(reply_to_list)
    return kwargs


def send_mail(subject, message, from_email, recipient_list, priority='medium', fail_silently=False, auth_user=None,
              auth_password=None, headers=None, attachments=None, content_object=None, tag=None, template_slug=None,
              reply_to_list=None):
    """
    Function to queue e-mails
    """

    from django.utils.encoding import force_text
    from django.core.mail import EmailMessage

    from mailer.models import Message

    subject = force_text(subject)
    message = force_text(message)

    email_obj = EmailMessage(**get_email_message_kwargs(subject, message, from_email, recipient_list, reply_to_list,
                                                        attachments, headers))

    return Message.objects.create_from_email_obj(subject, recipient_list, reply_to_list, email_obj, attachments,
                                                 priority, tag, template_slug, content_object)


def send_html_mail(subject, message, message_html, from_email, recipient_list, priority='medium', fail_silently=False,
                   auth_user=None, auth_password=None, headers=None, attachments=None, content_object=None, tag=None,
                   template_slug=None, reply_to_list=None):
    """
    Function to queue HTML e-mails
    """

    from django.utils.encoding import force_text
    from django.core.mail import EmailMultiAlternatives

    from mailer.models import Message

    subject = force_text(subject)
    message = force_text(message)
    message_html = force_text(message_html)

    email_obj = EmailMultiAlternatives(**get_email_message_kwargs(subject, message, from_email, recipient_list,
                                                                  reply_to_list, attachments, headers))
    email_obj.attach_alternative(message_html, 'text/html')

    return Message.objects.create_from_email_obj(subject, recipient_list, reply_to_list, email_obj, attachments,
                                                 priority, tag, template_slug, content_object)
