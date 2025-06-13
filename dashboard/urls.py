from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('get_emails/', views.get_emails, name='get_emails'),
]

