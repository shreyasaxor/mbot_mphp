from django.core.mail import EmailMessage

from django.core.mail import EmailMessage


from django.conf import settings
from Dsproject.settings import EMAIL_HOST_USER
import os
import requests
from django.template.loader import render_to_string



def _sendemail(to_email,hours,afile_path=None):
    print()
    try:
        ctx ={"name":"shreyas venkatramanappa","hours":hours}
        msg_body =render_to_string('emailtemplate.html',ctx)
        msg = EmailMessage('Scrapped files ', msg_body, EMAIL_HOST_USER, [to_email])
        msg.content_subtype = "html"
        msg.attach_file(os.path.join(settings.MEDIA_ROOT,afile_path+'.csv'))
        msg.send()
        sucess=True
    except:
        sucess=False
        import sys
        print(sys.exc_info())
    return sucess





import csv
def create_csv(results,filepath=None):

    result_dict = results

    try:
        with open('media/'+filepath+'.csv', 'w') as f:  # Just use 'w' mode in 3.x


            writer = csv.DictWriter(f, fieldnames=["Effort", "TEST_ID", "TEST_STATUS","TestCase"])
            writer.writeheader()


            for data in result_dict:
                writer.writerow({'Effort': data['Effort'], 'TEST_ID': data['TEST_ID'], 'TEST_STATUS': data['TEST_STATUS'],"TestCase":data['TestCase']})

        f.close()
    except:
        import sys
        print(sys.exc_info())

    return True

def efforts_time(results):
    sum =0;
    for x  in results:
        sum+=float(x['Effort'])

    return sum








def chech_mail(email_from,email_subject,email_body):

    API_TEST="http://127.0.0.1:8000/testcase/"

    if(email_subject in 'test'):
        data = {"query":email_body,"include_common": "true"}
        print(data,"datatatatttattatat <>>>>>>>>>>>>>>>>>>>")

        # sending post request and saving response as response object
        try:
            test_case = requests.post(url=API_TEST, data=data)
            print(test_case)
        except:
            import sys

            print(sys.exc_info())
        else:
            print("dfdsfsdfsdfds tetststststststsing")
            print(test_case.status_code)
            if test_case.status_code == 200:
                print(test_case.json(),">>>>>>>>>>>>>>>")
                print(test_case.text,"LLLLLLLLLLLL")


                if create_csv(test_case.json(),email_from):
                    time = efforts_time(test_case.json())/60
                    _sendemail(email_from,time,email_from)
    #
    #
    # class YourAutoReplyer(AutoReplyer):
    #     imap_server = 'your.imap.server'
    #     imap_port = 1234  # Custom port, only use if the default one doesn’t work.
    #     imap_user = 'your.imap.user@may-be-the-email-or-not.com'
    #     imap_password = 'your_password'
    #     smtp_server = 'your.smtp.server'
    #     smtp_port = 5678  # Custom port, only use if the default one doesn’t work.
    #     smtp_user = 'your.smtp.user@may-be-the-email-or-not.com'
    #     smtp_password = 'your_password'
    #     from_address = 'Your Displayed Name <your-email@address.com>'
    #     body = '''
    #     Hello,
    #     I’m on vacation until a date I should mention here.
    #     You’ll have an answer when I’m back.
    #     Call Django in case of emergency.
    #     Have a nice day,
    #     You
    #     '''
    #     body_html = '''
    #     <p>Hello</p>,
    #     <p>
    #         I’m on vacation until a date I should mention here.<br />
    #         You’ll have an answer when I’m back.<br />
    #         Call <a href="tel:+1234567890">Django</a> in case of emergency.
    #     </p>
    #     <p>
    #         Have a nice day,<br />
    #         You
    #     </p>
    #     '''
    # YourAutoReplyer().run()


from email import message_from_bytes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from imaplib import IMAP4, IMAP4_SSL, IMAP4_PORT, IMAP4_SSL_PORT
from smtplib import SMTP, SMTP_SSL, SMTP_PORT, SMTP_SSL_PORT
from subprocess import call
from textwrap import dedent
from time import sleep


__author__ = 'Bertrand Bordage'
__copyright__ = 'Copyright © 2016 Bertrand Bordage'
__license__ = 'MIT'


class AutoReplyer:
    refresh_delay = 5  # seconds

    imap_server = "imap.gmail.com"
    imap_use_ssl = True
    imap_port = IMAP4_PORT
    imap_ssl_port = IMAP4_SSL_PORT
    imap_user = None
    imap_password = None

    smtp_server = None
    smtp_use_ssl = False
    smtp_port = SMTP_PORT
    smtp_ssl_port = SMTP_SSL_PORT
    smtp_user = None
    smtp_password = None

    from_address = None
    body = None
    body_html = None

    def __init__(self):
        if self.imap_use_ssl:
            self.imap = IMAP4_SSL(self.imap_server, self.imap_ssl_port)
        else:
            self.imap = IMAP4(self.imap_server, self.imap_port)
        self.imap.login(self.imap_user, self.imap_password)
        if self.smtp_use_ssl:
            self.smtp = SMTP_SSL(self.smtp_server, self.smtp_ssl_port)
        else:
            self.smtp = SMTP(self.smtp_server, self.smtp_port)
        self.smtp.login(self.smtp_user, self.smtp_password)

    def close(self):
        self.smtp.close()
        self.imap.logout()

    def create_auto_reply(self, original):
        mail = MIMEMultipart('alternative')
        mail['Message-ID'] = make_msgid()
        mail['References'] = mail['In-Reply-To'] = original['Message-ID']
        mail['Subject'] = 'Re: ' + original['Subject']
        mail['From'] = self.from_address
        mail['To'] = original['Reply-To'] or original['From']
        mail.attach(MIMEText(dedent(self.body), 'plain'))
        mail.attach(MIMEText(self.body_html, 'html'))
        return mail

    def send_auto_reply(self, original):
        self.smtp.sendmail(
            self.from_address, [original['From']],
            self.create_auto_reply(original).as_bytes())
        log = 'Replied to “%s” for the mail “%s”' % (original['From'],
                                                     original['Subject'])
        print(log)
        try:
            call(['notify-send', log])
        except FileNotFoundError:
            pass

    def reply(self, mail_number):
        self.imap.select(readonly=True)
        _, data = self.imap.fetch(mail_number, '(RFC822)')
        self.imap.close()
        self.send_auto_reply(message_from_bytes(data[0][1]))
        self.imap.select(readonly=False)
        self.imap.store(mail_number, '+FLAGS', '\\Answered')
        self.imap.close()

    def check_mails(self):
        self.imap.select(readonly=False)
        _, data = self.imap.search(None, '(UNSEEN UNANSWERED)')
        self.imap.close()
        for mail_number in data[0].split():
            self.reply(mail_number)

    def run(self):
        try:
            while True:
                self.check_mails()
                sleep(self.refresh_delay)
        finally:
            self.close()
