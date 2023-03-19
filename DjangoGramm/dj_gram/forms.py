from PIL import Image
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm, ClearableFileInput, ImageField, PasswordInput, ModelMultipleChoiceField, CharField


from .models import *


class MultipleTagsForm(ModelForm):
    tag = CharField(widget=forms.Textarea, max_length=32, required=False)

    class Meta:
        model = Post
        fields = ['tag']

    def clean_tag(self):
        tags = self.cleaned_data.get('tag')
        if not tags:
            return tags

        clear_tags = self.parse_tags(tags)
        if clear_tags:
            return clear_tags

    def parse_tags(self, tags: str):
        if '#' in tags:
            clear_tags = set()
            tags = tags.replace(',', '').replace('.', '').split()

            for tag in tags:
                if tag.startswith('#'):
                    clear_tags.add(tag)

            if clear_tags:
                return clear_tags
            self.add_error('tag', ValidationError('No tags were found. Tags must start with "#".'))

        else:
            self.add_error('tag', ValidationError('No tags were found. Tags must start with "#".'))


class TagForm(ModelForm):
    class Meta:
        model = Tag
        fields = ('name',)

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name.startswith('#') or len(name) == 1:
            self.add_error('name', ValidationError('Tag must starts with "#" and contain characters.'))

        return name.split()[0]

    def clean(self):
        self._validate_unique = False
        return self.cleaned_data


class ImageForm(ModelForm):
    class Meta:
        model = Images
        fields = ('image',)

        widgets = {
            'image': ClearableFileInput(attrs={'multiple': True}),
        }


class CustomUserCreationForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email',)

    # def __init__(self, *args, **kwargs):
    #     super(UserCreationForm, self).__init__(*args, **kwargs)
    #     del self.fields['password1']
    #     del self.fields['password2']


class CustomUserFillForm(ModelForm):
    password1 = forms.CharField(widget=PasswordInput())
    password2 = forms.CharField(widget=PasswordInput())

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'bio', 'avatar')

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')

        try:
            password_validation.validate_password(password1, self.instance)
        except forms.ValidationError as error:
            self.add_error('password1', error)
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password1', ValidationError("Passwords don't match"))
        return password1
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class CustomUserAdminCreateForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ('email',)

