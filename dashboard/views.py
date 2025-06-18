from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .mail_checker import insert_and_show_recent_emails
from .models import EmailAccount, EmailMessage
# from django.core.cache import cache
from datetime import datetime, timedelta
from .helper import group_emails_by_app_email, get_num_accounts

# Create your views here.
@login_required
def index(request):
    """
    View for the dashboard index page
    """
    if not request.user.is_authenticated:
        return redirect('accounts:login_page')
    # For regular page load, just render the template
    accounts = EmailAccount.objects.all()
    num_gmail, num_outlook, num_yahoo, num_aol = get_num_accounts(accounts)
    context = {
        'num_gmail': num_gmail,
        'num_outlook': num_outlook,
        'num_yahoo': num_yahoo,
        'num_aol': num_aol,
        'total_accounts': num_gmail + num_outlook + num_yahoo + num_aol
    }
    return render(request, 'dashboard/index.html', context)

def check_spam(folder, host, num_spam, num_inbox):
    try:
        if host == 'imap.gmail.com':
            if str(folder).find('Junk') > -1 or str(folder).find('Spam') > -1:
                num_spam['gmail'] += 1
            elif str(folder).find('INBOX') > -1:
                num_inbox['gmail'] += 1
        elif host == 'imap-mail.outlook.com':
            if str(folder).find('Junk') > -1 or str(folder).find('Spam') > -1:
                num_spam['outlook'] += 1
            elif str(folder).find('INBOX') > -1:
                num_inbox['outlook'] += 1
        elif host == 'imap.mail.yahoo.com':
            if str(folder).find('Junk') > -1 or str(folder).find('Spam') > -1:
                num_spam['yahoo'] += 1
            elif str(folder).find('INBOX') > -1:
                num_inbox['yahoo'] += 1
        elif host == 'imap.aol.com':
            if str(folder).find('Junk') > -1 or str(folder).find('Spam') > -1:
                num_spam['aol'] += 1
            elif str(folder).find('INBOX') > -1:
                num_inbox['aol'] += 1
    except Exception as e:
        print('error', e)
        return

# @login_required
# def get_emails(request):
#     """
#     View to get emails
#     """
#     all_emails = []
#     period = request.GET.get('period', '7')  # Default to 7 days if not specified
    
#     # Calculate the cutoff date based on the period
#     cutoff_date = datetime.now()
#     if period != 'all':
#         cutoff_date = cutoff_date - timedelta(days=int(period))
#     accounts = EmailAccount.objects.filter(user=request.user)
#     num_gmail = 0
#     num_outlook = 0
#     num_yahoo = 0
#     num_aol = 0
#     num_spam = {
#         'gmail': 0,
#         'outlook': 0,
#         'yahoo': 0,
#         'aol': 0
#     }
#     num_inbox = {
#         'gmail': 0,
#         'outlook': 0,
#         'yahoo': 0,
#         'aol': 0
#     }
#     for acc in accounts:
#         try:
#             email_id = acc.id
#             if acc.imap_host_name == 'imap.gmail.com':
#                 num_gmail += 1
#             elif acc.imap_host_name == 'imap-mail.outlook.com':
#                 num_outlook += 1
#             elif acc.imap_host_name == 'imap.mail.yahoo.com':
#                 num_yahoo += 1
#             elif acc.imap_host_name == 'imap.aol.com':
#                 num_aol += 1
#             # Filter emails based on the period
#             if period == 'all':
#                 emails = EmailMessage.objects.filter(email_account=acc).order_by('-date')
#             else:
#                 emails = EmailMessage.objects.filter(
#                     email_account=acc,
#                     date__gte=cutoff_date
#                 ).order_by('-date')
            
#             # Convert EmailMessage objects to dictionaries
#             email_list = []
#             for email in emails:
#                 check_spam(email.folder, email.email_account.imap_host_name, num_spam, num_inbox)
#                 email_dict = {
#                     'app_mail': email.email_account.email_address,
#                     'subject': email.subject,
#                     'from': email.sender,
#                     'date': email.date.isoformat(),
#                     'body': email.body,
#                     'folder': email.folder,
#                     'host': email.email_account.imap_host_name,
#                     'name': email.name,
#                     'sender_email': email.sender_email
#                 }
#                 email_list.append(email_dict)
#             all_emails.extend(email_list)
            
#             if not emails:
#                 emails = insert_and_show_recent_emails(acc)
#                 if emails:
#                     all_emails.extend(emails)
#         except Exception as e:
#             print('error', e)
#             continue
#     all_emails = group_emails_by_app_email(all_emails)
#     return JsonResponse({
#         'all_emails': all_emails,
#         'num_gmail': num_gmail,
#         'num_outlook': num_outlook,
#         'num_yahoo': num_yahoo,
#         'num_aol': num_aol,
#         'total_accounts': num_gmail + num_outlook + num_yahoo + num_aol,
#         'num_spam': num_spam,
#         'num_inbox': num_inbox
#     }, safe=False)

@login_required
def search_emails(request):
    """
    View to search emails
    """
    if request.method == 'GET':
        num_gmail = 0
        num_outlook = 0
        num_yahoo = 0
        num_aol = 0
        num_spam = {
            'gmail': 0,
            'outlook': 0,
            'yahoo': 0,
            'aol': 0
        }
        num_inbox = {
            'gmail': 0,
            'outlook': 0,
            'yahoo': 0,
            'aol': 0
        }
        keyword = request.GET.get('keyword')
        if(str(keyword).find('@') > -1):
            emails = EmailMessage.objects.filter(sender_email__icontains=keyword)
        else:
            emails = EmailMessage.objects.filter(name__icontains=keyword)
        accounts = EmailAccount.objects.all()
        
        for acc in accounts:
            if(acc.imap_host_name == 'imap.gmail.com'):
                num_gmail += 1
            elif(acc.imap_host_name == 'imap-mail.outlook.com'):
                num_outlook += 1
            elif(acc.imap_host_name == 'imap.mail.yahoo.com'):
                num_yahoo += 1
            elif acc.imap_host_name == 'imap.aol.com':
                num_aol += 1
        # Convert QuerySet to list of dictionaries
        email_list = []
        for email in emails:
            check_spam(email.folder, email.email_account.imap_host_name, num_spam, num_inbox)
            email_dict = {
                'app_mail': email.email_account.email_address,
                'subject': email.subject,
                'from': email.sender,
                'date': email.date.isoformat(),
                'body': email.body,
                'folder': email.folder,
                'name': email.name,
                'sender_email': email.sender_email,
                'host': email.email_account.imap_host_name
            }
            email_list.append(email_dict)
        email_list = group_emails_by_app_email(email_list)
        return JsonResponse({
            'emails': email_list,
            'num_gmail': num_gmail,
            'num_outlook': num_outlook,
            'num_yahoo': num_yahoo,
            'num_aol': num_aol,
            'total_accounts': num_gmail + num_outlook + num_yahoo + num_aol,
            'num_spam': num_spam,
            'num_inbox': num_inbox
        })
    return JsonResponse({
        'error': 'Invalid request method'
    })