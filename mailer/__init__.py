VERSION = (2, 0, 2)


def get_version():
    return '.'.join(map(str, VERSION))

__version__ = get_version()


# replacement for django.core.mail.send_mail


def send_mail(subject, message, from_email, recipient_list, priority='medium', fail_silently=False, auth_user=None,
              auth_password=None, headers=None, attachments=None, content_object=None, tag=None, template_slug=None,
              reply_to_list=None):
    """
    Function to queue e-mails
    """

    from django.utils.encoding import force_text
    from django.core.mail import EmailMessage
    from mailer.models import Message, PRIORITY_MAPPING, STATUS_PENDING, STATUS_DEBUG

    headers = headers or {}
    priority = PRIORITY_MAPPING[priority]
    subject = force_text(subject)
    message = force_text(message)

    email_obj = EmailMessage(
        subject=subject,
        body=message,
        from_email=from_email,
        to=recipient_list,
        attachments=attachments,
        headers=headers,
        reply_to=reply_to_list
    )
    db_msg = Message(
        status=STATUS_PENDING if not getattr('MAILER_DEBUG', False) else STATUS_DEBUG,
        priority=priority,
        subject=subject,
        content_object=content_object,
        tag=tag,
        template_slug=template_slug
    )
    db_msg.email = email_obj
    db_msg.set_recipients(recipient_list)
    db_msg.set_reply_to(reply_to_list)
    db_msg.save()
    return db_msg


def send_html_mail(subject, message, message_html, from_email, recipient_list, priority='medium', fail_silently=False,
                   auth_user=None, auth_password=None, headers=None, attachments=(), content_object=None, tag=None,
                   template_slug=None, reply_to_list=None):
    """
    Function to queue HTML e-mails
    """

    from django.utils.encoding import force_text
    from django.core.mail import EmailMultiAlternatives
    from mailer.models import Message, PRIORITY_MAPPING, STATUS_PENDING, STATUS_DEBUG

    headers = headers or {}
    priority = PRIORITY_MAPPING[priority]
    # need to do this in case subject used lazy version of ugettext
    subject = force_text(subject)
    message = force_text(message)
    message_html = force_text(message_html)

    email_obj = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=from_email,
        to=recipient_list,
        attachments=attachments,
        headers=headers,
        reply_to=reply_to_list
    )
    email_obj.attach_alternative(message_html, 'text/html')
    db_msg = Message(
        status=STATUS_PENDING if not getattr('MAILER_DEBUG', False) else STATUS_DEBUG,
        priority=priority,
        subject=subject,
        content_object=content_object,
        tag=tag,
        template_slug=template_slug
    )
    db_msg.email = email_obj
    db_msg.set_recipients(recipient_list)
    db_msg.set_reply_to(reply_to_list)
    db_msg.save()

    for attachment in attachments:
        db_msg.attachments.create(file=attachment)

    return db_msg
