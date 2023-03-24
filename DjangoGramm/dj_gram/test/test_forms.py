from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
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
        """Pass to form obviously unvalid password to test validation"""
        password1 = 'foo'
        form = CustomUserFillForm(data={'password1': password1})

        with self.assertRaises(forms.ValidationError):
            form.is_valid()

    #  testing password2
    def test_custom_field_password2(self):
        password1 = CustomUserFillForm().fields['password2']
        widget = password1.widget

        self.assertIsInstance(password1, forms.CharField)
        self.assertIsInstance(widget, PasswordInput)
  
    def test_clean_password2(self):
        password1 = 'VERY strong PASSWORD'
        password2 = 'VERY strong PASSWORD'
        form = CustomUserFillForm(data={'password1': password1, 'password2': password2})

        form.is_valid()
        password1 = form.cleaned_data['password1']
        password2 = form.cleaned_data['password2']
        self.assertEqual(password1, password2)

    def test_password2_validation_is_present(self):
        password1 = 'VERY strong PASSWORD'
        password1 = 'mismatched_pass'
        form = CustomUserFillForm(data={'password1': password1, 'password2': password2})

        with self.assertRaises(ValidationError):
            form.is_valid()

        self.assertEqual(form.errors['password2'][0], "Passwords don't match")
    
    #  testing save
    def test_save():
        avatar = SimpleUploadedFile('avatar.jpg', b'')
        password = 'VERY strong PASSWORD'
        fields = ('first_name', 'last_name', 'bio', 'avatar')
        values = ('John', 'Doe', 'About me', avatar)
        data = dict(zip(fields, values))
        data['password1'] = password
        data['password2'] = password

        user = CustomUser.objects.get(id=1)
        form = CustomUserFillForm(data=data, instance=user)
        
        for value, field in enumerate(fields):
            with self.subTest():
                self.assertEqual(getattr(user, field), values[value])
        
        self.assertTrue(user.check_password(password))
    
    


        



    

























