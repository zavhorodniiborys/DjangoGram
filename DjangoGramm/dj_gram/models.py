from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AbstractUser
from django.db import models


class Profile(models.Model):
    full_name = models.CharField(max_length=128)
    bio = models.TextField(max_length=512)
    avatar = models.BinaryField()


class BUser(AbstractUser):
    pass


class CustomUser(AbstractBaseUser):
    email = models.EmailField(verbose_name='mail', max_length=127, unique=True)
    pass_hash = models.CharField(max_length=511)
    full_name = models.CharField(max_length=128)
    bio = models.TextField(max_length=512)
    avatar = models.BinaryField()
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)


class User(models.Model):
    mail = models.CharField(max_length=64, unique=True, null=False)
    pass_hash = models.CharField(max_length=512)
    profile_id = models.OneToOneField(Profile, on_delete=models.CASCADE, null=True)


class Post(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='posts')
    tag = models.TextField(max_length=256)
    date = models.DateTimeField(auto_now_add=True)
# todo localtime

class Vote(models.Model):
    profile = models.ForeignKey(Profile, related_name='votes', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='votes', on_delete=models.CASCADE)
    vote = models.BooleanField()

    class Meta:
        unique_together = ('profile_id', 'post_id')


class Images(models.Model):
    image = models.ImageField()
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
