from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('registration/', views.registration),
    path('add_post/', views.add_post),
    path('confirm_email/<uidb64>/<token>/', views.confirm_email, name='confirmation'),
]
