from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

from . import views
urlpatterns = [
    path('registration/', views.Registration.as_view(), name='registration'),
    path('confirm_email/<uidb64>/<umailb64>/<token>/', views.FillProfile.as_view(), name='fill_profile'),
    path('user/<int:pk>', views.ProfilePage.as_view(), name='profile'),
    path('user/<int:pk>/edit', views.EditProfilePage.as_view(), name='edit_profile'),
    path('user/<int:followed_user_id>/<str:action>', views.Subscribe.as_view(), name='subscribe'),
    path('add_post/', views.add_post, name='add_post'),
    path('feed/', views.Feed.as_view(), name='feed'),
    path('post/<int:pk>', views.ViewPost.as_view(), name='view_post'),
    path('post/<int:pk>/delete', views.DeletePost.as_view(), name='delete_post'),
    path('post/<int:post_id>/add_tag', views.AddTag.as_view(), name='add_tag'),
    path('post/<int:post_id>/vote/<int:vote>', views.vote, name='vote'),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    # re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

app_name = 'dj_gram'

