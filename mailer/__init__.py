VERSION = (1, 0, 3)


def get_version():
    return '.'.join(map(str, VERSION))

__version__ = get_version()


# replacement for django.core.mail.send_mail


def send_mail(subject, message, from_email, recipient_list, priority="medium", fail_silently=False, auth_user=None,
              auth_password=None, headers={}, attachments=None):
    """
    Function to queue e-mails
    """

    from django.utils.encoding import force_text
    from django.core.mail import EmailMessage
    from mailer.models import Message, PRIORITY_MAPPING
    
    priority = PRIORITY_MAPPING[priority]
    subject = force_text(subject)
    message = force_text(message)

    email_obj = EmailMessage(
        subject=subject,
        body=message,
        from_email=from_email,
        to=recipient_list,
        attachments=attachments,
        headers=headers
    )
    db_msg = Message(
        priority=priority,
        subject=subject
    )
    db_msg.email = email_obj
    db_msg.set_recipients(recipient_list)
    db_msg.save()
    return db_msg

    return 1


def send_html_mail(subject, message, message_html, from_email, recipient_list, priority="medium", fail_silently=False,
                   auth_user=None, auth_password=None, headers={}, attachments=None):
    """
    Function to queue HTML e-mails
    """

    from django.utils.encoding import force_text
    from django.core.mail import EmailMultiAlternatives
    from mailer.models import Message, PRIORITY_MAPPING

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
        headers=headers
    )
    email_obj.attach_alternative(message_html, "text/html")
    db_msg = Message(
        priority=priority,
        subject=subject
    )
    db_msg.email = email_obj
    db_msg.set_recipients(recipient_list)
    db_msg.save()

    return 1
