import re

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm, ClearableFileInput, ImageField, PasswordInput, ModelMultipleChoiceField, CharField, \
    Textarea

from .models import *


class TagFormMixin:
    """
    Mixin for parsing and saving tags.
    Use multiple = True to parse and save more than one tag in string.
    Tags must start with '#'.
    """
    def parse_tags(self, multiple: bool):
        tags = self.cleaned_data.get('name').lower()

        if multiple:
            tags = re.findall(r'#(\w{2,})\b', tags)
        else:
            tags = re.search(r'#(\w{2,})\b', tags)
            if not tags:
                raise ValidationError('Wrong tag format. Tag must start with "#".')
            tags = ''.join(tags.group(1))  # group(1) because re.search includes "#"
        return tags

    def save_one_tag(self, tag: str, post):
        if Tag.objects.filter(name=tag).count():
            tag = Tag.objects.get(name=tag)
        else:
            tag = Tag.objects.create(name=tag)

        tag.posts.add(post)

    def save_multiple_tags(self, tags: list, post):
        for _tag in tags:
            self.save_one_tag(tag=_tag, post=post)

    def save(self, post, multiple: bool):
        if not isinstance(post, Post):
            raise ValidationError('Please attach post to tags')

        parsed_tags = self.parse_tags(multiple)

        if multiple:
            self.save_multiple_tags(tags=parsed_tags, post=post)
        else:
            self.save_one_tag(tag=parsed_tags, post=post)


class MultipleTagsForm(TagFormMixin, ModelForm):
    name = CharField(widget=Textarea(attrs={'rows': 10, 'cols': 20}), max_length=180, required=False)

    class Meta:
        model = Tag
        fields = ('name',)


class TagForm(TagFormMixin, ModelForm):
    class Meta:
        model = Tag
        fields = ('name',)

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

