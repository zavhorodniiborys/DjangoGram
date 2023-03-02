from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('register/', views.Register.as_view()),
    path('add_post/', views.add_post),
]
