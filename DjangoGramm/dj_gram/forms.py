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
