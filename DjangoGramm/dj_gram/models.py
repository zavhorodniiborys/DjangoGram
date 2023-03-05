from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class Profile(models.Model):
    full_name = models.CharField(max_length=128)
    bio = models.TextField(max_length=512)
    avatar = models.BinaryField()


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
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
    email = models.EmailField(verbose_name='email address', unique=True)
    bio = models.TextField(max_length=512)
    avatar = models.BinaryField()

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


# class CustomUser(AbstractBaseUser):
#     email = models.EmailField(verbose_name='mail', max_length=127, unique=True)
#     pass_hash = models.CharField(max_length=511)
#     full_name = models.CharField(max_length=128)
#     is_active = models.BooleanField(default=True)
#     is_admin = models.BooleanField(default=False)


# class User(models.Model):
#     mail = models.CharField(max_length=64, unique=True, null=False)
#     pass_hash = models.CharField(max_length=512)
#     profile_id = models.OneToOneField(Profile, on_delete=models.CASCADE, null=True)


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
