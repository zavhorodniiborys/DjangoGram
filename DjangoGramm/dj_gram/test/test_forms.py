from unittest.mock import patch

from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.core.exceptions import ValidationError as DJValidationError
from django.test import TestCase, override_settings
from django.contrib.auth import password_validation

from ..forms import *
from .conf import TEST_DIR, create_test_image


class TestImageForm(TestCase):
    def test_image_widget(self):
        form = ImageForm()
        widget_is_multiple = form.fields['image'].widget.attrs['multiple']
        self.assertTrue(widget_is_multiple)

    def test_model_is_Images(self):
        model = ImageForm._meta.model
        self.assertTrue(model, Images)

    def test_image_is_required(self):
        form = ImageForm()
        required = form.fields['image'].required
        self.assertTrue(required)

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_valid_form(self):
        image = create_test_image()
        files = {'image': image.open()}
        form = ImageForm(data=None, files=files)

        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        files = {'image': b'wrong data'}
        form = ImageForm(data=None, files=files)

        self.assertFalse(form.is_valid())


class TestCustomUserCreationForm(TestCase):
    def test_fields_is_email(self):
        field = CustomUserCreationForm._meta.fields
        self.assertEqual(field, ('email',))

    def test_model_is_CustomUser(self):
        model = CustomUserCreationForm._meta.model
        self.assertEqual(model, CustomUser)

    def test_valid_form(self):
        data = {'email': 'foo@foo.bar'}
        form = CustomUserCreationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        data = {'email': 'wrong data'}
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())

    def test_empty_form(self):
        form = CustomUserCreationForm(data={'email': None})
        form.is_valid()
        self.assertInHTML('<ul class="errorlist"><li>This field is required.</li></ul>', str(form.errors['email']))


class TestCustomUserFillForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        CustomUser.objects.create_user(email='foo@foo.foo')

    def test_model_is_CustomUserModel(self):
        model = CustomUserFillForm._meta.model
        self.assertEqual(model, CustomUser)

    def test_meta_fields(self):
        expected_res = ('first_name', 'last_name', 'bio', 'avatar')
        form_fields = CustomUserFillForm()._meta.fields
        self.assertEqual(form_fields, expected_res)

    #  testing password1
    def test_custom_field_password1(self):
        password1 = CustomUserFillForm().fields['password1']
        widget = password1.widget

        self.assertIsInstance(password1, forms.CharField)
        self.assertIsInstance(widget, PasswordInput)

    def test_clean_password1(self):
        expected_res = 'VERY strong PASSWORD'
        form = CustomUserFillForm(data={'password1': expected_res})
        form.is_valid()
        res = form.cleaned_data['password1']

        self.assertEqual(res, expected_res)

    def test_password1_validation_is_present(self):
        """Pass to form obviously invalid password to test validation"""
        password1 = 'foo'
        form = CustomUserFillForm(data={'password1': password1})
        form.is_valid()

        self.assertEqual(form.errors['password1'][0], 'This password is too short. It must contain at least 8 '
                                                      'characters.')

    #  testing password2
    def test_custom_field_password2(self):
        password1 = CustomUserFillForm().fields['password2']
        widget = password1.widget

        self.assertIsInstance(password1, forms.CharField)
        self.assertIsInstance(widget, PasswordInput)

    def test_clean_password2_returns_cleaned_password(self):
        password = 'VERY strong PASSWORD'
        fields = ('first_name', 'last_name', 'bio', 'password1', 'password2')
        values = ('John', 'Doe', 'About me', password, password)
        data = dict(zip(fields, values))

        form = CustomUserFillForm(data=data, files={'avatar': create_test_image()})
        form.is_valid()
        cleaned_res = form.cleaned_data['password2']
        self.assertEqual(cleaned_res, password)

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_password2_validation_is_present(self):
        password1 = 'VERY strong PASSWORD'
        password2 = 'mismatched_pass'
        form = CustomUserFillForm(data={'password1': password1, 'password2': password2})
        form.is_valid()

        self.assertEqual(form.errors['password2'][0], "Passwords don't match")

    # testing save
    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_save(self):
        avatar = create_test_image()
        password = 'VERY strong PASSWORD'
        fields = ('first_name', 'last_name', 'bio')
        values = ('John', 'Doe', 'About me')
        data = dict(zip(fields, values))
        data['password1'] = password
        data['password2'] = password

        user = CustomUser.objects.get(id=1)
        form = CustomUserFillForm(data=data, files={'avatar': avatar.open()}, instance=user)
        self.assertTrue(form.is_valid())
        form.save()

        for value, field in enumerate(fields):
            with self.subTest():
                self.assertEqual(getattr(user, field), values[value])

        self.assertEqual(user.avatar.url, '/media/images/avatars/IMAGE.jpg')
        self.assertTrue(user.check_password(password))


class TestMultipleTagsForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='foo@foo.foo')
        Post.objects.create(user=user)

    #  testing Meta
    def test_model_is_Tag(self):
        model = MultipleTagsForm._meta.model
        self.assertEqual(model, Tag)

    def test_name_field(self):
        field = MultipleTagsForm().fields['name']
        widget = field.widget
        max_length = field.max_length
        required = field.required

        self.assertIsInstance(field, CharField)
        self.assertIsInstance(widget, Textarea)
        self.assertEqual(max_length, 180)
        self.assertFalse(required)

    def test_parse_multiple_tags(self):
        bad_tag = '#Very-b^d_t@:@g'
        form = MultipleTagsForm(data={'name': bad_tag})
        form.is_valid()
        res = form.parse_tags(multiple=True)

        self.assertEqual(res, ['very'])

    def test_save_validation_error(self):
        post = Post.objects.get(id=1)
        form = MultipleTagsForm(data={'name': '#tag'})
        form.is_valid()
        self.failureException(forms.ValidationError, form.save(post=post, multiple=True))

    def test_save(self):
        post = Post.objects.get(id=1)
        form = MultipleTagsForm(data={'name': '#tag, #foo'})
        form.is_valid()
        form.save(post=post, multiple=True)
        first_tag = post.tags.get(name='tag').name
        second_tag = post.tags.get(name='foo').name

        self.assertEqual(first_tag, 'tag')
        self.assertEqual(second_tag, 'foo')


class TestTagForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='foo@foo.foo')
        Post.objects.create(user=user)

    #  testing Meta
    def test_model_is_Tag(self):
        model = TagForm._meta.model
        self.assertEqual(model, Tag)

    def test_fields(self):
        fields = TagForm._meta.fields
        self.assertEqual(fields, ('name',))

    #  testing clean
    def test_validate_unique(self):
        is_validate_unique = TagForm()._validate_unique
        self.assertFalse(is_validate_unique)

    def test_tag_already_exists(self):
        tag = Tag.objects.create(name='#tag')
        post = Post.objects.get(id=1)
        tag.posts.add(post)

        form = TagForm(data={'name': '#tag'})
        form.is_valid()
        form.save(post=post, multiple=False)
        new_tag = Tag.objects.get(id=1)

        self.assertEqual(new_tag, tag)

    def test_clean_returns_cleaned_data(self):
        form = TagForm(data={'name': '#tag'})
        form.is_valid()
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data, {'name': '#tag'})

    def test_parse_name(self):
        bad_tag = '#Very-b#^@d #tag'
        form = TagForm(data={'name': bad_tag})
        form.is_valid()
        tag = form.parse_tags(multiple=False)
        self.assertEqual(tag, 'very')

    #  testing save
    def test_save_validation_error(self):
        form = TagForm(data={'name': '#tag'})
        with self.assertRaises(ValidationError):
            form.save(post=CustomUser, multiple=False)

    def test_save(self):
        post = Post.objects.get(id=1)
        form = TagForm(data={'name': '#tag'})
        form.is_valid()
        form.save(post=post, multiple=False)
        new_tag = post.tags.get(name='tag').name

        self.assertEqual(new_tag, 'tag')
