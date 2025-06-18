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