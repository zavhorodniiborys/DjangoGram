from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('register/', views.register),
    path('add_post/', views.add_post),
]
