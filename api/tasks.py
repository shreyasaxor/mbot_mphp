import string

from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from celery import shared_task
import smtplib
import imaplib
import logging


import email

import requests
from django.conf import settings
from celery import shared_task
from api.utils import chech_mail



@shared_task
def create_random_user_accounts():
    print("shreyas")
    try:
        results = {}
        mail = imaplib.IMAP4_SSL(settings.EMAIL_HOST)
        print(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.select('inbox')
        type, data = mail.search(None, 'UNSEEN')
        if data != ['']:
            mail_ids = data[0]
            id_list = mail_ids.split()
            if len([int(x.decode("utf-8")) for x in id_list]) > 0:
                first_email_id = int(id_list[0].decode("utf-8"))
                latest_email_id = int(id_list[-1].decode("utf-8"))
                for i in range(latest_email_id, first_email_id - 1, -1):
                    print(i)
                    type, data = mail.fetch(str(i), '(RFC822)')
                    for response_part in data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_string(response_part[1].decode("utf-8"))
                            f = msg['from']
                            email_subject = msg['subject']
                            email_from = f[f.find("<") + 1:f.find(">")]
                            if msg.is_multipart():
                                for p in msg.walk():
                                    if p.get_content_type() == "text/plain":
                                        email_body = p.get_payload()
                                        # email_subject = p.get_subject()
                                        # srt = list(str(email_body))
                                        # msg_bdy = ''.join(srt)
                                        # print(srt)
                                        # print(msg_bdy)
                                        print(email_from)
                                        print(email_subject)
                                        print(email_body)
                                        chech_mail(email_from,email_subject,email_body,i)



                            else:
                                pass
            else:
                results = {'meassage': 'no new messages'}


        else:
            results = {'meassage': 'no new messages'}

    except Exception as e:
        import sys, os
        print(sys.exc_info())
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

    return results



from django.core.mail import EmailMessage


from django.conf import settings
from Dsproject.settings import EMAIL_HOST_USER
import os

from django.template.loader import render_to_string


# @shared_task()



