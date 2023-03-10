from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'dj_gram'

urlpatterns = [
    path('', views.index),
    path('registration/', views.registration),
    path('add_post/', views.add_post),
    path('feed/', views.feed, name='feed'),
    path('confirm_email/<uidb64>/<umailb64>/<token>/', views.fill_profile, name='confirmation'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
