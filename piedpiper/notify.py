# coding=utf-8

"""
Minimalistic module to send email notifications
"""

import re as re
import smtplib as smtplib
from email.mime.text import MIMEText


def send_email_notification(to_addr, from_addr, subject, body, smtp='localhost'):
    """

    :param to_addr:
    :param from_addr:
    :param subject:
    :param body:
    :param smtp:
    :return:
    """
    # this is a simplified version to identify common address
    # patterns - we all know that there is no reg exp that matches
    # all valid email addresses ;-)
    RE_EMAIL_ADDR = "^[\w\.-]+@[\w\.-]+\.\w{2,5}$"
    assert re.search(RE_EMAIL_ADDR, to_addr) is not None and\
        re.search(RE_EMAIL_ADDR, from_addr) is not None,\
        'Presumably invalid email address detected: to {} - from {}'.format(to_addr, from_addr)
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    s = smtplib.SMTP(smtp)
    s.send_message(msg)
    s.quit()
    return