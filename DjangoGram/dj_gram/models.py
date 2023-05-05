import os
import sys
from io import BytesIO

import cloudinary
from PIL import Image
from cloudinary.models import CloudinaryField
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import m2m_changed, pre_delete
from django.dispatch import receiver


class ImageThumbnailMixin:
    @staticmethod
    def make_thumbnail(image_field):
        acceptable_image_size = (1280, 720)
        image = Image.open(image_field).convert('RGB')
        image.thumbnail(acceptable_image_size)
        temp = BytesIO()  # because thumbnail must be saved in binary mode
        image.save(temp, 'jpeg')
        temp.seek(0)  # sets the file's start position
        image_field.file = temp
        image_field.size = sys.getsizeof(temp)


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


class CustomUser(ImageThumbnailMixin, AbstractUser):
    username = None
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    email = models.EmailField(verbose_name='email address', unique=True, max_length=255)
    bio = models.TextField(max_length=512)
    avatar = CloudinaryField('image', folder=os.path.join('images', 'avatars'), use_filename=True)
    follow_count = models.IntegerField(default=0)
    followed_count = models.IntegerField(default=0)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if 'update_fields' in kwargs:
            if 'avatar' in kwargs['update_fields']:
                self.make_thumbnail(image_field=self.avatar)

        super().save(*args, **kwargs)


class Follow(models.Model):
    user = models.ForeignKey(CustomUser, related_name='follower', on_delete=models.CASCADE)
    followed_id = models.ForeignKey(CustomUser, related_name='followed', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'followed_id')


class Post(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')
    date = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(to='Tag', related_name='posts', blank=True)
    max_tags_count = 5

    def get_likes(self):
        return self.votes.filter(vote=1).count()

    def get_dislikes(self):
        return self.votes.filter(vote=0).count()

    class Meta:
        ordering = ['-id']

    def save(self, *args, **kwargs):
        super(Post, self).save(*args, **kwargs)


class Vote(models.Model):
    user = models.ForeignKey(CustomUser, related_name='votes', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='votes', on_delete=models.CASCADE)
    vote = models.BooleanField()

    class Meta:
        unique_together = ('user', 'post')


class Images(ImageThumbnailMixin, models.Model):
    post = models.ForeignKey(Post, related_name='images', on_delete=models.CASCADE)
    image = CloudinaryField('image', folder=os.path.join('images', 'posts'), use_filename=True)
    max_count_images_in_post = 10

    class Meta:
        verbose_name = 'image'
        verbose_name_plural = 'images'

    def validate_count_images_in_post(self):
        images_count = self.post.images.all().count()
        if images_count >= Images.max_count_images_in_post:
            raise ValidationError(f'Post can\'t have more than {Images.max_count_images_in_post} images')

    def save(self, *args, **kwargs):
        self.validate_count_images_in_post()
        self.make_thumbnail(self.image)
        super(Images, self).save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=16, unique=True)

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(Tag, self).save(*args, **kwargs)


@receiver(m2m_changed, sender=Post.tags.through)
def validate_count_tags_in_post(sender, action, **kwargs):
    if action == 'pre_add':
        instance = kwargs['instance']
        # print(kwargs['pk_set'])
        pk = list(kwargs['pk_set'])[0]

        if isinstance(instance, Post):
            tags_count = instance.tags.all().count()
        elif isinstance(instance, Tag):
            tags_count = Post.objects.get(id=pk).tags.all().count()

        if tags_count >= Post.max_tags_count:
            raise ValidationError(f'Post can\'t have more than {Post.max_tags_count} tags')


@receiver(pre_delete, sender=CustomUser)
def delete_image_in_cloud(sender, instance, **kwargs):
    cloudinary.uploader.destroy(instance.avatar.public_id, invalidate=True)


@receiver(pre_delete, sender=Images)
def delete_image_in_cloud(sender, instance, **kwargs):
    cloudinary.uploader.destroy(instance.image.public_id, invalidate=True)
