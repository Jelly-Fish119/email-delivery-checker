# === STEP 1: Add all your email accounts here ===
# accounts = [
#     {"email": "traviscaldw@gmail.com", "password": "jlgr dpgu cybi xlmj", "host": "imap.gmail.com"},
#     {"email": "amandarober15@gmail.com", "password": "jews zkib eckz pmlp", "host": "imap.gmail.com"},
#     {"email": "larrywright1644@gmail.com", "password": "rdhy yxob pxfb nyvv", "host": "imap.gmail.com"},
#     {"email": "elaineriley1970@gmail.com", "password": "fzeo krhz pmko wlts", "host": "imap.gmail.com"},
#     {"email": "johannalove2012@gmail.com", "password": "yoix vqit zkdn ibrb", "host": "imap.gmail.com"},
#     {"email": "cdgnxdfh6@hotmail.com", "password": "etre zrxw fmkc poin", "host": "imap-mail.outlook.com"},
#     {"email": "johannalove2012@yahoo.com", "password": "yoix vqit zkdn ibrb", "host": "imap.mail.yahoo.com"},
#     {"email": "johannalove2012@aol.com", "password": "yoix vqit zkdn ibrb", "host": "imap.aol.com"},
# ]

# === STEP 2: Function to monitor one email account ===
import imaplib
from email import message_from_bytes
from email.header import decode_header
import threading
import time
import queue
from datetime import datetime
from .models import EmailMessage, EmailAccount

def get_email_content(msg):
    """Extract email content from message"""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode()
                except:
                    return "Unable to decode content"
    else:
        try:
            return msg.get_payload(decode=True).decode()
        except:
            return "Unable to decode content"
    return ""

def get_emails_checker(email, password, host, folders=['INBOX', '[Gmail]/Spam'], since_days=7):
    from datetime import datetime, timedelta
    all_emails = []
    try:
        mail = imaplib.IMAP4_SSL(host)
        mail.login(email, password)

        since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")

        for folder in folders:
            mail.select(folder)
            status, data = mail.uid('search', None, f'(SINCE {since_date})')
            if status != 'OK':
                continue

            uids = data[0].split()
            if not uids:
                continue

            uids_str = b','.join(uids)
            result, fetch_data = mail.uid('fetch', uids_str, '(RFC822)')
            if result != 'OK':
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

                    email_data = {
                        'subject': str(subject),
                        'from': str(from_addr),
                        'date': str(email_message.get('Date')),
                        'body': str(content),
                        'folder': folder,
                        'host': host,
                    }
                    all_emails.append(email_data)

        return all_emails
    except Exception as e:
        # print('error', e)
        return None
    
def insert_all_emails_background(account):
    # Insert everything (no SINCE filter)
    try:
        full_emails = get_emails_checker(
            email=account["email"],
            password=account["password"],
            host=account["host"],
            since_days=3650  # Fetch last 10 years as "all"
        )
        # Save to DB or queue
        if full_emails is None:
            return None
        for email_data in full_emails:
            try:
                insert_to_db(email_data, account)  # Your DB save logic
            except Exception as e:
                # print('error', e)
                continue
    except Exception as e:
        # print('error', e)
        return None


def insert_and_show_recent_emails(account):
    recent_emails = get_emails_checker(
        email=account["email"],
        password=account["password"],
        host=account["host"],
        since_days=7
    )
    for email_data in recent_emails:
        try:
            insert_to_db(email_data, account["email"])
        except Exception as e:
            # print('error', e)
            continue
    return recent_emails  # This can be shown in UI immediately

def insert_to_db(email_data, acc_email):
    # Save to DB or queue
    account = EmailAccount.objects.get(email_address=acc_email).first()
    try:
        EmailMessage.objects.create_or_update(
            email_account=account.id,
            subject=email_data['subject'],
            body=email_data['body'],
            sender=email_data['from'],
            receiver=email_data['to'],
        )
    except Exception as e:
        # print('error', e)
        return None
    return email_data

