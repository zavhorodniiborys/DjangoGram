import os
from io import BytesIO

from PIL import Image
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import m2m_changed


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
    follow_count = models.IntegerField(default=0)
    followed_count = models.IntegerField(default=0)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


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
        # self.validate_count_tags_in_post()
        super(Post, self).save(*args, **kwargs)


class Vote(models.Model):
    user = models.ForeignKey(CustomUser, related_name='votes', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='votes', on_delete=models.CASCADE)
    vote = models.BooleanField()

    class Meta:
        unique_together = ('user', 'post')


class Images(models.Model):
    def upload_path(self, filename):
        return os.path.join('images', 'post', str(self.post.id), filename)

    post = models.ForeignKey(Post, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=upload_path)
    max_count_images_in_post = 10

    class Meta:
        verbose_name = 'image'
        verbose_name_plural = 'images'

    def validate_count_images_in_post(self):
        images_count = self.post.images.all().count()
        if images_count >= Images.max_count_images_in_post:
            raise ValidationError(f'Post can\'t have more than {Images.max_count_images_in_post} images')

    def make_thumbnail(self):
        acceptable_image_size = (1280, 720)
        image = Image.open(self.image).convert('RGB')
        image_name = self.image.name

        image.thumbnail(acceptable_image_size)

        temp = BytesIO()  # because thumbnail must be saved in binary mode
        image.save(temp, 'jpeg')
        temp.seek(0)  # sets the file's start position

        self.image.save(image_name, ContentFile(temp.read()), save=False)  # ContentFile reads file as string of bytes

    def save(self, *args, **kwargs):
        self.validate_count_images_in_post()
        self.make_thumbnail()

        super(Images, self).save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True)

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(Tag, self).save(*args, **kwargs)


def validate_count_tags_in_post(sender, action, **kwargs):
    if action == 'pre_add':
        instance = kwargs['instance']

        if isinstance(instance, Post):
            tags_count = instance.tags.all().count()
        elif isinstance(instance, Tag):
            tags_count = instance.posts.all().count()

        if tags_count >= Post.max_tags_count:
            raise ValidationError(f'Post can\'t have more than {Post.max_tags_count} tags')


m2m_changed.connect(validate_count_tags_in_post, sender=Post.tags.through)
