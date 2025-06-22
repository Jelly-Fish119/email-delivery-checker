import ssl
from imapclient import IMAPClient
from email import message_from_bytes
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime, timedelta
from .models import EmailMessage, EmailAccount
import pytz

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
    all_emails = []
    try:
        context = ssl.create_default_context()
        with IMAPClient(host, ssl=True, ssl_context=context) as client:
            client.login(email, password)
            print(email, '-' * 30)

            # Define cutoff datetime
            if since_mins:
                since_date = datetime.now() - timedelta(minutes=since_mins)
            elif since_hours:
                since_date = datetime.now() - timedelta(hours=since_hours)
            else:
                since_date = datetime.now() - timedelta(days=since_days)

            since_for_search = since_date.date()  # IMAP only uses date

            for folder in folders:
                try:
                    client.select_folder(folder)
                    print('📂 Folder:', folder)
                except Exception as e:
                    print(f"⚠️ Failed to select folder {folder}: {e}")
                    continue

                messages = client.search(["SINCE", since_for_search])
                if not messages:
                    continue

                response = client.fetch(messages, ["BODY.PEEK[HEADER]"])
                for msgid, data in response.items():
                    raw_headers = data[b'BODY[HEADER]']
                    try:
                        msg = message_from_bytes(raw_headers)
                    except Exception as e:
                        print(f"❌ Failed to parse email: {e}")
                        continue

                    try:
                        email_date = parsedate_to_datetime(msg.get("Date"))
                        if email_date and email_date < since_date:
                            continue  # Skip older than target datetime
                    except:
                        continue

                    subject = decode_mime_words(msg.get("Subject"))
                    from_header = msg.get("From", "")
                    from_full = decode_mime_words(from_header)
                    name, sender_email = parseaddr(from_full)

                    email_data = {
                        'subject': subject,
                        'from': from_full,
                        'date': str(email_date),
                        'body': "",  # body can be fetched in second pass or omitted
                        'folder': folder,
                        'host': host,
                        'name': name,
                        'sender_email': sender_email,
                    }
                    all_emails.append(email_data)

        return all_emails

    except Exception as e:
        print('❌ General error:', e)
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

