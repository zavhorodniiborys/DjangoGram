import re

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.forms import ModelForm, ClearableFileInput, PasswordInput, CharField, Textarea, EmailField, EmailInput

from .models import *


class TagFormMixin:
    """
    Mixin for parsing and saving tags.
    Use multiple = True to parse and save more than one tag in string.
    Tags must start with '#'.
    """

    @staticmethod
    def validate_tag_length(tag):
        max_length = Tag._meta.get_field('name').max_length
        if len(tag) > max_length:
            raise ValidationError(f'Tag is too long. Max length is {max_length}')

    def clean_name(self):
        tags = self.cleaned_data.get('name', None).lower()
        if tags:
            if self.multiple_tags_allowed:
                tags = re.findall(r'#(\w{2,})\b', tags)
                for tag in tags:
                    self.validate_tag_length(tag)
            else:
                tags = re.search(r'#(\w{2,})\b', tags)
                if tags:
                    tags = ''.join(tags.group(1))  # group(dj_gram_dev.env) because re.search includes "#"

            if not tags:
                self.add_error('name', 'Wrong tag format. Tags must start with "#" and contain at least 2 characters.')
        return tags

    def save_one_tag(self, tag: str, post):
        if Tag.objects.filter(name=tag).exists():
            tag = Tag.objects.get(name=tag)
        else:
            tag = Tag.objects.create(name=tag)

        try:
            tag.posts.add(post)
        except ValidationError:
            self.add_error('name', f'Post can have up to {Post.max_tags_count} tags.')

    def save_multiple_tags(self, tags: list, post):
        for _tag in tags:
            self.save_one_tag(tag=_tag, post=post)

    def save(self, post, *args, **kwargs):
        if not isinstance(post, Post):
            raise ValidationError('Please attach post to tags')

        parsed_tags = self.cleaned_data.get('name')

        if not parsed_tags:
            return

        if self.multiple_tags_allowed:
            self.save_multiple_tags(tags=parsed_tags, post=post)
        else:
            self.save_one_tag(tag=parsed_tags, post=post)


class MultipleTagsForm(TagFormMixin, forms.Form):
    name = CharField(widget=Textarea(attrs={'rows': 10, 'cols': 20}), max_length=180, required=False, label='Tags')

    def __init__(self, *args, **kwargs):
        self.multiple_tags_allowed = True
        super(MultipleTagsForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        return super().clean_name()

    def save(self, post, *args, **kwargs):
        super().save(post=post, *args, **kwargs)


class TagForm(TagFormMixin, ModelForm):
    class Meta:
        model = Tag
        fields = ('name',)

    def __init__(self, *args, **kwargs):
        self.multiple_tags_allowed = False
        super(TagForm, self).__init__(*args, **kwargs)
        self.fields['name'].initial = '#'

    def clean(self):
        self._validate_unique = False
        return self.cleaned_data

    def save(self, post, *args, **kwargs):
        super().save(post=post, multiple=False, *args, **kwargs)


class ImageForm(ModelForm):
    class Meta:
        model = Images
        fields = ('image',)

        widgets = {
            'image': ClearableFileInput(attrs={'multiple': True}),
        }

    def clean_image(self):
        if len(self.files.getlist('image')) > 10:
            self.add_error('image', f'Post can have up to {Images.max_count_images_in_post} images.')
        return self.cleaned_data.get('image')

    def save(self, post=None):
        if not post:
            raise ValidationError('Please attach post to images')

        for image in self.files.getlist('image'):
            Images.objects.create(image=image, post=post)


class CustomUserCreationForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email',)

        widgets = {
            'email': EmailInput(attrs={'class': 'form-control', 'placeholder': ' '}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        if commit:
            user.save()
        return user


class CustomUserFillForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].label = 'Avatar'
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'bio', 'avatar')

    def save(self, commit=True):
        user = super(CustomUserFillForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = True

        if commit:
            self.changed_data.remove('password1')
            self.changed_data.remove('password2')
            self.changed_data.extend(['password', 'is_active'])
            user.save(update_fields=self.changed_data)
        return user


class CustomUserChangeForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ('avatar', 'first_name', 'last_name', 'bio')
        widgets = {
            'avatar': forms.FileInput(),
            'bio': forms.Textarea(attrs={'id': 'bio'})
        }

    def save(self, commit=True):
        self.instance.save(update_fields=self.changed_data)

        return self.instance


class CustomUserAdminCreateForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ('email',)

