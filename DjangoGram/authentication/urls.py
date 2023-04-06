from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.LoginUser.as_view(), name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
]
