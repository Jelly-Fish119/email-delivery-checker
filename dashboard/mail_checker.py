import imaplib
from imapclient import IMAPClient
from email import message_from_bytes, utils
from email.header import decode_header
from datetime import datetime, timedelta
from .models import EmailMessage, EmailAccount
from email.utils import parsedate_to_datetime
import pytz
import ssl

def get_email_content(email_message):
    body = ""
    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode(errors='ignore')
                    break
                except:
                    continue
    else:
        try:
            body = email_message.get_payload(decode=True).decode(errors='ignore')
        except:
            pass
    return body

def get_emails_checker(email, password, host, folders=['INBOX', '[Gmail]/Spam'], since_days=3650, since_mins=None, since_hours=None):
    all_emails = []
    try:
        context = ssl.create_default_context()
        with IMAPClient(host, ssl=True, ssl_context=context) as client:
            client.login(email, password)
            print(email, '-'*30, '\n')

            since_date = None
            if since_days:
                since_date = datetime.now() - timedelta(days=since_days)
            elif since_mins:
                since_date = datetime.now() - timedelta(minutes=since_mins)
            elif since_hours:
                since_date = datetime.now() - timedelta(hours=since_hours)
            else:
                since_date = datetime.now() - timedelta(days=3650)

            for folder in folders:
                try:
                    client.select_folder(folder)
                    print('folder', folder)
                except Exception as e:
                    print(f"Failed to select folder {folder}: {e}")
                    continue

                messages = client.search(["SINCE", since_date])
                if not messages:
                    continue

                response = client.fetch(messages, ["RFC822"])
                for msgid, data in response.items():
                    raw_email = data[b'RFC822']
                    try:
                        email_message = message_from_bytes(raw_email)
                    except Exception as e:
                        print("Failed to parse email:", e)
                        continue

                    subject = decode_header(email_message.get('Subject'))[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(errors='ignore')

                    from_addr = decode_header(email_message.get('From'))[0][0]
                    if isinstance(from_addr, bytes):
                        from_addr = from_addr.decode(errors='ignore')

                    content = get_email_content(email_message)
                    name, sender_email = utils.parseaddr(from_addr)
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
        # First try using email.utils.parsedate_to_datetime which is designed for email dates
        return parsedate_to_datetime(date_str)
    except Exception as e:
        try:
            # If that fails, try parsing with datetime.strptime
            # Remove the 'GMT' and replace with '+0000' for proper timezone format
            date_str = date_str.replace('GMT', '+0000')
            return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        except Exception as e:
            # If all parsing fails, return current time
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

