# A function to return the date of the email

def get_date(email_message):
    return email_message['date']

# A function to return the subject of the email

def get_subject(email_message):
    return email_message['subject']

def group_emails_by_app_email(emails):
    result = [];
    temp_email_with_one_app_email = {};
    # Group emails by app_email
    email_groups = {}
    host_groups = {}
    # First group all emails by app_email
    for email in emails:
        app_email = email.get('app_mail')
        host = email.get('host')
        if app_email not in email_groups:
            email_groups[app_email] = []
            host_groups[app_email] = host
        email_groups[app_email].append(email)
    
    # Convert grouped emails into desired format
    # Take only first 3 emails for each app_email
    for app_email, email_list in email_groups.items():
        length = len(email_list)
        count = int(length / 3)
        if(length % 3 > 0):
            count += 1
        for i in range(count):
            result.append({
                "app_email": app_email,
                "host": host_groups[app_email],
                "emails": email_list[i*3:(i+1)*3]
            })
    return result;

def get_num_accounts(accounts):
    num_gmail = 0
    num_outlook = 0
    num_yahoo = 0
    num_aol = 0
    for acc in accounts:
        if(acc.imap_host_name == 'imap.gmail.com'):
            num_gmail += 1
        elif(acc.imap_host_name == 'imap-mail.outlook.com'):
            num_outlook += 1
        elif(acc.imap_host_name == 'imap.mail.yahoo.com'):
            num_yahoo += 1
        elif acc.imap_host_name == 'imap.aol.com':
            num_aol += 1
    return num_gmail, num_outlook, num_yahoo, num_aol

def group_emails_by_host(accounts):
    result = [];
    email_groups = {
        'gmail': [],
        'outlook': [],
        'yahoo': [],
        'aol': []
    }
    for acc in accounts:
        host = acc.imap_host_name
        if host == 'imap.gmail.com':
            email_groups['gmail'].append(acc)
        elif host == 'imap-mail.outlook.com':
            email_groups['outlook'].append(acc)
        elif host == 'imap.mail.yahoo.com':
            email_groups['yahoo'].append(acc)
        elif host == 'imap.aol.com':
            email_groups['aol'].append(acc)
    return email_groups