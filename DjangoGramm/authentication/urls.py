from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
]
