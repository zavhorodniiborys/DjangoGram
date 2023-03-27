import re

from PIL import Image
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm, ClearableFileInput, ImageField, PasswordInput, ModelMultipleChoiceField, CharField, \
    Textarea

from .models import *


class TagFormMixin:
    def parse_tags(self, multiple):
        tags = self.cleaned_data['name'].lower()

        if multiple:
            tags = re.findall(r'#(\w{2,})\b', tags)
        else:
            tags = re.search(r'#(\w{2,})\b', tags)
            tags = ''.join(tags.group())

        return tags

    def save_one_tag(self, tag: str, post):
        if Tag.objects.filter(name=tag).count():
            tag = Tag.objects.get(name=tag)
        else:
            tag = Tag.objects.create(name=tag)

        tag.posts.add(post)

    def save_multiple_tags(self, parsed_tags: list, post):
        for _tag in parsed_tags:
            self.save_one_tag(tag=_tag, post=post)

    def save(self, post, multiple):
        if not post:
            raise ValidationError('Please attach post to tags')
        
        if multiple:
            self.save_multiple_tags(parsed_tags, post)
        else:
            self.save_one_tag(tag=parsed_tags, post=post)

        #parsed_tags = self.parse_name()

        #if isinstance(parsed_tags, list):
        #    self.save_multiple_tags(parsed_tags, post)

        #elif isinstance(parsed_tags, str):
        #    self.save_one_tag(tag=parsed_tags, post=post)


class MultipleTagsForm(TagFormMixin, ModelForm):
    name = CharField(widget=Textarea(attrs={'rows': 10, 'cols': 20}), max_length=180, required=False)

    class Meta:
        model = Tag
        fields = ('name',)


class TagForm(TagFormMixin, ModelForm):
    class Meta:
        model = Tag
        fields = ('name',)

    #def parse_name(self):
    #    tags = self.cleaned_data['name'].lower()
    #    tags = re.search(r'#(\w{2,})\b', tags)
    #    tags = ''.join(tags.group())
    #    return tags

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

    def save(self, post=None):
        if not post:
            raise ValidationError('Please attach post to images')

        for image in self.files.getlist('image'):
            Images.objects.create(image=image, post=post)


class CustomUserCreationForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email',)


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
            self.add_error('password2', ValidationError("Passwords don't match"))
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

