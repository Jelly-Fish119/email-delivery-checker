from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from accounts.models import UserSession
from django.contrib.sessions.models import Session
from django.utils import timezone

def login_view(request):
    if request.method == 'GET':
        return render(request, 'accounts/login.html')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            # Check for existing sessions for this user
            active_sessions = Session.objects.filter(
                expire_date__gte=timezone.now()
            ).exclude(session_key=request.session.session_key)
            
            for session in active_sessions:
                if session.get_decoded().get('_auth_user_id') == str(user.id):
                    messages.error(request, 'This user is already logged in another device')
                    return render(request, 'accounts/login.html')
            
            login(request, user)
            messages.success(request, 'Login successful')
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Username is not valid or password is incorrect')
    return render(request, 'accounts/login.html')

def logout_view(request):
    if request.method == 'GET':
        return render(request, 'accounts/logout.html')
    if request.user.is_authenticated:
        Session.objects.filter(user=request.user).delete()
        UserSession.objects.filter(user=request.user).delete()
    logout(request)
    return redirect('login_page')