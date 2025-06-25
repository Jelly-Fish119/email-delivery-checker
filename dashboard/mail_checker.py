import ssl
from imapclient import IMAPClient
import socket
from imapclient.exceptions import IMAPClientError
from email import message_from_bytes
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime, timedelta
from .models import EmailMessage, EmailAccount
import pytz
import time
import imaplib
import threading


MAX_IDLE_TIME = 900  # 15 minutes for safety (below Gmail's 29 min limit)
RECONNECT_DELAY = 1  # delay before reconnect attempt


def decode_mime_words(header):
    decoded = decode_header(header or '')
    return ''.join(
        part.decode(enc or 'utf-8', errors='ignore') if isinstance(part, bytes) else part
        for part, enc in decoded
    )

def get_email_content(email_message):
    # Return plain text or HTML fallback
    for part in email_message.walk():
        content_type = part.get_content_type()
        if content_type == "text/plain" and part.get_payload(decode=True):
            return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
        elif content_type == "text/html" and part.get_payload(decode=True):
            return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
    return ""

def get_emails_checker(email, password, host, folders=['INBOX', '[Gmail]/Spam'], since_days=3650, since_mins=None, since_hours=None):
    from datetime import datetime, timedelta
    all_emails = []
    try:
        mail = imaplib.IMAP4_SSL(host)
        mail.login(email, password)
        print(email, '-'*30, '\n')
        since_date = None
        if since_days:
            since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
        elif since_mins:
            print('-'*40, 'minute')
            since_date = (datetime.now() - timedelta(minutes=since_mins)).strftime("%d-%b-%Y")
        elif since_hours:
            since_date = (datetime.now() - timedelta(hours=since_hours)).strftime("%d-%b-%Y")
        

        for folder in folders:
            mail.select(folder)
            print('folder', folder)
            status, data = mail.uid('search', None, f'(SINCE {since_date})')
            if status != 'OK':
                continue

            uids = data[0].split()
            if not uids:
                continue

            uids_str = b','.join(uids)
            try:    
                result, fetch_data = mail.uid('fetch', uids_str, '(RFC822)')
                if result != 'OK':
                    continue
            except Exception as e:
                print('error', e)
                continue

            for i in range(0, len(fetch_data), 2):
                if isinstance(fetch_data[i], tuple):
                    raw_email = fetch_data[i][1]
                    try:
                        email_message = message_from_bytes(raw_email)
                    except:
                        continue

                    subject = decode_header(email_message.get('Subject'))[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(errors='ignore')

                    from_addr = decode_header(email_message.get('From'))[0][0]
                    if isinstance(from_addr, bytes):
                        from_addr = from_addr.decode(errors='ignore')

                    content = get_email_content(email_message)
                    name, sender_email = parseaddr(from_addr)
                    name, encoding = decode_header(name)[0]
                    if isinstance(name, bytes):
                        name = name.decode(encoding or 'utf-8', errors='ignore')

                    email_data = {
                        'subject': str(subject),
                        'from': str(from_addr),
                        'date': str(email_message.get('Date')),
                        'body': str(content),
                        'folder': folder,
                        'host': host,
                        'name': name,
                        'sender_email': sender_email
                    }
                    all_emails.append(email_data)

        return all_emails
    except Exception as e:
        print('error', e)
        return None

def check_folders(host):
    if(host == 'imap.gmail.com'):
        return ['INBOX', '[Gmail]/Spam']
    elif(host == 'imap-mail.outlook.com'):
        return ['INBOX', 'Junk']
    elif(host == 'imap.mail.yahoo.com'):
        return ['INBOX', 'Bulk Mail']
    elif(host == 'imap.aol.com'):
        return ['INBOX', 'Spam']

    
def insert_all_emails_background(account):
    # Insert everything (no SINCE filter)
    try:
        full_emails = get_emails_checker(
            email=account.email_address,
            password=account.password,
            folders=check_folders(account.imap_host_name),
            host=account.imap_host_name,
            since_days=3650  # Fetch last 10 years as "all"
        )
        # Save to DB or queue
        if full_emails is None:
            return None
        for email_data in full_emails:
            try:
                insert_to_db(email_data, account)  # Your DB save logic
            except Exception as e:
                print('error', e)
                continue
    except Exception as e:
        print('error', e)
        return None


def insert_and_show_recent_emails(account):
    recent_emails = get_emails_checker(
        email=account.email_address,
        password=account.password,
        folders=check_folders(account.imap_host_name),
        host=account.imap_host_name,
        since_days=7
    )
    for email_data in recent_emails:
        try:
            insert_to_db(email_data, account.email_address)
        except Exception as e:
            print('error', e)
            continue
    return recent_emails  # This can be shown in UI immediately

def parse_email_date(date_str):
    try:
        return parsedate_to_datetime(date_str)
    except Exception as e:
        try:
            # Only call replace if date_str is a string
            if isinstance(date_str, str):
                date_str = date_str.replace('GMT', '+0000')
                print('date_str', date_str)
                return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
            else:
                # If it's a list, try to get the first element
                if isinstance(date_str, list) and date_str:
                    first_element = date_str[0]
                    if isinstance(first_element, str):  # Make sure the element is a string
                        print('first_element', first_element)
                        date_str = first_element.replace('GMT', '+0000')
                        return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
                return datetime.now(pytz.UTC)  # Return current time if conversion fails
        except Exception as e:
            return datetime.now(pytz.UTC)

def insert_to_db(email_data, acc_email):
    try:
        account = EmailAccount.objects.get(email_address=acc_email)
        
        # Parse the date properly
        date = parse_email_date(email_data.get('date', ''))
        
        if EmailMessage.objects.filter(email_account=account, subject=email_data['subject'], date=date).exists():
            return None
        else:
            EmailMessage.objects.create(
            email_account=account,
            subject=email_data['subject'],
            date=date,
            body=email_data['body'],
            sender=email_data['from'],
            folder=email_data.get('folder', ''),
            name=email_data.get('name', ''),
            sender_email=email_data.get('sender_email', '')
        )
    except Exception as e:
        print('error', e)
        return None
    return email_data

started_daemon = False

def listen_for_emails(email, password, host='imap.gmail.com', folder='INBOX'):
    import ssl
    from imapclient import IMAPClient
    from email import message_from_bytes
    from email.header import decode_header
    from email.utils import parseaddr, parsedate_to_datetime
    import time

    context = ssl.create_default_context()
    all_emails = []

    try:
        with IMAPClient(host, port=993, ssl=True, ssl_context=context) as client:
            print(f'🔐 Logging in {email} to {folder}')
            client.login(email.strip(), password.strip())
            client.select_folder(folder)

            while True:
                idle = client.idle()
                print(f"[{email} - {folder}] IDLE waiting for new emails...")
                responses = client.idle_check(timeout=MAX_IDLE_TIME)
                client.idle_done()

                if responses:
                    print(f"[{email} - {folder}] 📥 New email detected!")
                    messages = client.search(['UNSEEN'])
                    if messages:
                        response = client.fetch(messages, ["BODY.PEEK[HEADER]"])
                        for msgid, data in response.items():
                            raw_headers = data[b'BODY[HEADER]']
                            msg = message_from_bytes(raw_headers)
                            try:
                                email_date = parsedate_to_datetime(msg.get("Date"))
                            except:
                                continue
                            subject = decode_mime_words(msg.get("Subject"))
                            from_header = decode_mime_words(msg.get("From", ""))
                            name, sender_email = parseaddr(from_header)

                            email_data = {
                                'subject': subject,
                                'from': from_header,
                                'date': str(email_date),
                                'body': '',
                                'folder': folder,
                                'host': host,
                                'name': name,
                                'sender_email': sender_email
                            }

                            from .models import EmailAccount
                            acc = EmailAccount.objects.filter(email_address=email).first()
                            if acc:
                                from .mail_checker import insert_to_db
                                insert_to_db(email_data, acc.email_address)
                time.sleep(10)
    except (socket.error, EOFError, IMAPClientError) as e:
        print(f"❌ Connection lost on {email} - {folder}: {str(e)}")
        time.sleep(RECONNECT_DELAY)
    except Exception as e:
        print(f"[{email} - {folder}] ❌ Error: {e}")

def start_realtime_listeners():
    global started_daemon
    import sys
    if started_daemon or 'makemigrations' in sys.argv or 'migrate' in sys.argv:
        return
    started_daemon = True
    accounts = EmailAccount.objects.all()
    for account in accounts:
        folders = check_folders(account.imap_host_name)
        for folder in folders:
            threading.Thread(
                target=listen_for_emails,
                args=(account.email_address, account.password, account.imap_host_name, folder),
                daemon=True
            ).start()