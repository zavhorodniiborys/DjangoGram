import os
from io import BytesIO

from PIL import Image
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.files.base import ContentFile
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        extra_fields.setdefault("is_active", False)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractUser):
    username = None
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    email = models.EmailField(verbose_name='email address', unique=True, max_length=255)
    bio = models.TextField(max_length=512)
    avatar = models.ImageField(upload_to='images/avatars/')

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


class Post(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')
    date = models.DateTimeField(auto_now_add=True)
    tag = models.ManyToManyField(to='Tag', related_name='posts', blank=True)

    def get_likes(self):
        return self.votes.filter(vote=1).count()

    def get_dislikes(self):
        return self.votes.filter(vote=0).count()

    def __str__(self):
        return str(self.id)

    class Meta:
        ordering = ['-id']


class Vote(models.Model):
    profile = models.ForeignKey(CustomUser, related_name='votes', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='votes', on_delete=models.CASCADE)
    vote = models.BooleanField()

    class Meta:
        unique_together = ('profile_id', 'post_id')


class Images(models.Model):
    post = models.ForeignKey(Post, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=f'images/post/{post}')

    class Meta:
        verbose_name = 'image'
        verbose_name_plural = 'images'
    
    def save(self, *args, **kwargs):
        acceptable_image_size = (1280, 720)
        image = Image.open(self.image).convert('RGB')
        image_name = self.image.name

        image.thumbnail(acceptable_image_size)

        temp = BytesIO()  # because thumbnail must be saved in binary mode
        image.save(temp, 'jpeg')
        temp.seek(0)  # sets the file's start position

        self.image.save(image_name, ContentFile(temp.read()), save=False)  # ContentFile reads file as string of bytes
        super(Images, self).save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True)

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(Tag, self).save(*args, **kwargs)
