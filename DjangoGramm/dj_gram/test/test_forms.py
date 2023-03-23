from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.test import TestCase, override_settings
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

    # def test_empty_form(self):
    #     form = ImageForm(files={'image': SimpleUploadedFile('test', b'').open()})
    #     print(form)
    #     self.assertTrue(form.is_valid())

    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_valid_form(self):
        image = create_test_image()
        data = {'image': image.open()}
        form = ImageForm(data=None, files=data)

        self.assertTrue(form.is_valid())

#     def test_invalid_form(self):
#         data = {'image': b'wrong data'}
#         form = ImageForm(data=None, files=None)
#         form.is_valid()
#         print(form.cleaned_data)
#
#         self.assertFalse(form.is_valid())
#


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
    def test_model_is_CustomUserModel(self):
        model = CustomUserFillForm._meta.model
        self.assertEqual(model, CustomUser)

    def test_meta_fields(self):
        expected_res = ('first_name', 'last_name', 'bio', 'avatar')
        form_fields = CustomUserFillForm()._meta.fields
        self.assertEqual(form_fields, expected_res)

    def test_custom_field_password1(self):
        password1 = CustomUserFillForm().fields['password1']
        widget = password1.widget
        self.assertIsInstance(password1, forms.CharField)
        self.assertIsInstance(widget, PasswordInput)

    def test_custom_field_password2(self):
        password1 = CustomUserFillForm().fields['password2']
        widget = password1.widget
        self.assertIsInstance(password1, forms.CharField)
        self.assertIsInstance(widget, PasswordInput)

    # def test_clean_password1(self):
    #     expected_res = 'VERY strong PASSWORD'
    #     form = CustomUserFillForm(data={'password1': expected_res})
    #     print(form)
    #     res = form.clean_password1()
    #     self.assertEqual(res, expected_res)


