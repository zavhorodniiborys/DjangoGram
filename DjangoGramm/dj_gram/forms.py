from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.forms import ModelForm, ClearableFileInput

from .models import *


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['tag']


class ImageForm(ModelForm):
    class Meta:
        model = Images
        fields = ['image']

        widgets = {
            'image': ClearableFileInput(attrs={'multiple': True}),
        }


class CustomUserRegistrationMail(ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email',)


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email',)
        # exclude = ('password2',)

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        del self.fields['password1']
        del self.fields['password2']


class CustomUserCreateProfile(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'bio')


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        fields = '__all__'
        # exclude = ('email',)
