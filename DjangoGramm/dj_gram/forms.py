from django.contrib.auth.forms import UserCreationForm, UserChangeForm
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



class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = BUser
        fields = ('username', 'email')

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = BUser
        fields = ('username', 'email')
