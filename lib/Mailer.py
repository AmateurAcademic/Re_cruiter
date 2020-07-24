import os
import re
import sys
import json
import email
import atexit
import imaplib
import smtplib
import pydash as _
from os.path import basename
from langdetect import detect
from email.utils import formatdate, parsedate_tz
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from email_templates import get_email_templates
emailTemplates = get_email_templates()

class Mailer():
    ADDR_PATTERN = re.compile(r'[\'"]?([^<\'"]+)\s*[\'"]?\s*<(.*?)>|<(.*?)>')  # Finds email as <nospam@nospam.com>

    credentials = {}
    mail_connection = False
    emails = []
    sent_emails_cache = []

    servers = {
        'inbound': False,
        'outbound': False,
    }

    @property
    def already_sent_emails(self) -> list:
        if not self.sent_emails_cache:
            try:
                self.sent_emails_cache = pickle.load(open( f'files/{self.name}_sent_emails.pickle', 'rb')) #delete to run live
            except:
                return []
        return self.sent_emails_cache

    def __init__(self, name='unnamed', inbound=False, outbound=False, username=False, password=False):
        if username and password and inbound:
            self.credentials['username'] = username
            self.credentials['password'] = password
            self.servers['inbound'] = inbound
            self.servers['outbound'] = outbound
            self.connect(inbound, username, password)
        self.name = name

    def __getitem__(self, key):
        return self.emails[key]

    def __len__(self):
        return len(self.emails)

    def __maybe_decode(self, encodingTuple):
        try: 
            return encodingTuple[0].decode() 
        except: 
            return str(encodingTuple[0])

    def connect(self, server, username, password):
        mail_connection = imaplib.IMAP4_SSL(server)
        try:
            mail_connection.login(username, password)
            self.mail_connection = mail_connection
            print(f'Logged in to {username}\'s mailbox.')
        except imaplib.IMAP4.error:
            print("Failed to login")
            sys.exit()
        
        atexit.register(self.save_sent_emails)
        atexit.register(self.close)

    def close(self):
        try:
            self.mail_connection.close()
        finally:
            self.mail_connection.logout()

    def open_folder(self, folder_name):
        if self.mail_connection.state == "SELECTED":
            self.mail_connection.close()

        rv, data = self.mail_connection.select(folder_name)
        if rv == 'OK':
            print(f'Folder {folder_name} opened.')
        else:
            print("Could not open specified folder.")

    def copy_to(self, msg_uid, folder_name):
        result = self.mail_connection.uid('COPY', msg_uid, folder_name)
        return result[0] == 'OK'

    def move_to(self, msg_uid, folder_name):
        if self.copy_to(msg_uid, folder_name):
            mov, data = self.mail_connection.uid('STORE', msg_uid , '+FLAGS', '(\Deleted)')
            self.mail_connection.expunge()

    def fetch_message(self, msg_uid):
        rv, data = self.mail_connection.uid('fetch', msg_uid, "(RFC822)")
        if rv != 'OK':
            print("ERROR fetching message #", msg_uid)
            return {}

        self.raw_email = data[0][1]
        try:
             return email.message_from_string(data[0][1].decode('utf-8'))  # dict-like object
        except:
            return email.message_from_string(data[0][1].decode('windows-1252'))

    def extract_from_message(self, msg_parsed, fieldName):
        field = msg_parsed.get(fieldName, "")
        return field

    def get_email_ids(self, query='ALL'):
        if self.mail_connection.state != "SELECTED":
            raise imaplib.IMAP4.error("Cannot search without selecting a folder")

        rv, data = self.mail_connection.uid('search', None, query)
        if rv != 'OK':
            print ("Could not fetch email ids")  # for some reason...
            return []

        return data[0].split()

    def get_body(self, msg_parsed):
        import mailparser
        return mailparser.parse_from_bytes(self.raw_email).body

    def get_subject(self, msg_parsed):
        subject = self.extract_from_message(msg_parsed, 'Subject')
        subject = decode_header(subject)
        subject = ''.join(map(self.__maybe_decode, subject))
        return subject

    def get_recipients(self, msg_parsed):
        recipients = []
        field = self.extract_from_message(msg_parsed, 'From')
        if field:
            results = re.findall(Mailer.ADDR_PATTERN, field)
            if results:
                name, email, backup = results[0]
                recipients.extend([{ 'name': name.strip(), 'email': email + backup }])
            else:
                    recipients.extend([{ 'name': '', 'email': field }])
        return recipients

    def collect_emails(self, folder='INBOX', cutoff_date=False, limit=-1):
        limitCounter = 0
        skippedCounter = 0
        self.open_folder(folder)
        mail_filter = "(SINCE %s)" % cutoff_date if cutoff_date else 'ALL'
        msg_uid_list = self.get_email_ids(mail_filter)

        print(f'{len(msg_uid_list)} emails found.')
            
        # Fetch a list of recipients
        mails = []
        for msg_uid in msg_uid_list:
            skippedCounter = 0

            msg = self.fetch_message(msg_uid)
            subject = self.get_subject(msg)
            data = self.get_recipients(msg)
            body = self.get_body(msg)
            
            try:
                if data:
                    data = data[0]
                    data['subject'] = subject
                    data['domain'] = data['email'].split('@')[1]
                    nameparts = data['name'].split(' ')
                    data['firstname'] = nameparts[0]
                    data['message'] = body
                    
                    if len(nameparts) > 1:
                        data['lastname'] = nameparts[1]
                        
                    data['language'] = 'en'

                    data['date'] = parsedate_tz(msg['Date'])
                    
                    if detect(data['subject']) == 'de': # or detect(data['message']) == 'de':
                        data['language'] = 'de'
                    
                    mails.extend([data])
                
                    if limit > -1:
                        if limitCounter >= limit:
                            break
                        limitCounter += 1
            except:
                skippedCounter += 1
                print('Email could not be fetched. Skipping.')
                break

        print(f"{len(mails)} processed. {skippedCounter} emails had to be skipped;")

        self.emails = mails
        return self

    def load_emails(self, filename=False):
        if not filename:
            filename = f'{self.name}_emails'
        self.emails = json.load(open(filename + '.json', 'r'))
        print(f'All mails loaded from "{filename}.json".')
        return self


    def save_emails(self, filename=False):
        if not filename:
            filename = f'{self.name}_emails'
        json.dump(self.emails, open(filename + '.json', 'w'), indent=4)
        print(f'All mails saved in "{filename}.json".')
        return self

    def save_sent_emails(self):
        if(self.sent_emails_cache):
            return pickle.dump(self.sent_emails_cache, open(f'files/{self.name}_sent_emails.pickle', 'wb'))

    def send_email(self, email, data):
        print('Connecting to', self.servers['outbound'], '…')
        with smtplib.SMTP(self.servers['outbound'], 587) as server:
            server.starttls()
            server.login(self.credentials['username'], self.credentials['password'])
            
            if type(data['to']) is list:
                data['to'] = ', '.join(data['to'])
            
            message = MIMEMultipart()
            message['From'] = data['from']
            message['To']   = data['to']
            message['Date'] = formatdate(localtime=True)
            message['Subject'] = data['subject']

            message.attach(MIMEText(email))

            for f in data['files'] or []:
                with open(f, "rb") as file:
                    part = MIMEApplication(file.read(),Name=basename(f))
                part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
                message.attach(part)
            
            server.sendmail(data['from'], data['to'], message.as_string())
            self.sent_emails_cache.append(data['to'])

        print('Email sent.')
        return self

class MailTemplate():
    def __init__(self, template, data):
        template = _.get(emailTemplates, template, '')
        self.template = template
        tags = re.findall(r'#\{\s*([^}]+)\s*\}', template)
        uniqueTags = list(set(tags))
        
        for tag in uniqueTags:
            value = data[tag]
            if type(value) is list:
                value = ', '.join(value)
                
            template = re.sub(r'#\{%s\}' % tag, value, template)
        self.rendered = template