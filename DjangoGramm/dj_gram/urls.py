from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'dj_gram'

urlpatterns = [
    path('registration/', views.Registration.as_view(), name='registration'),
    path('add_post/', views.add_post, name='add_post'),
    path('feed/', views.Feed.as_view(), name='feed'),
    path('post/<int:pk>', views.ViewPost.as_view(), name='view_post'),
    path('post/<int:post_id>/add_tag', views.AddTag.as_view(), name='add_tag'),
    path('post/<int:post_id>/vote/<int:vote>', views.vote, name='vote'),
    path('confirm_email/<uidb64>/<umailb64>/<token>/', views.FillProfile.as_view(), name='fill_profile'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
