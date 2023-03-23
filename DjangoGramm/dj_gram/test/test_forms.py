from django.test import TestCase
from ..forms import *

class TestImageForm(TestCase):
    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    @classmethod
    def setUpTestData(cls):
        image = cls.create_image()

    @staticmethod
    def create_test_image():
        image = Image.new('RGB', size=(100, 100))
        temp = BytesIO()
        image.save(temp, 'jpeg')
        image.close()

        temp_image = InMemoryUploadedFile(file=temp, field_name=None, name='IMAGE.jpg',
                                          content_type='image/jpeg',
                                          size=image.size, charset=None)
        return temp_image
        
    def test_image_widget(self):
        form = ImageForm()
        widget_is_multiple = form.fields['image'].widget.ClearableFileInput.multiple
        self.assertTrue(widget_is_multiple)
    
    def test_model_is_Images(self):
        model = ImageForm._meta.model
        self.assertIsInstance(model, Images)

    def test_empty_form(self):
        form = ImageForm()
        self.assertIn()
    
    def test_valid_form(self):
        image = create_image()
        data = {'image': image}
        form = ImageForm(files=data)

        self.assertTrue(form.is_valid())
    
    def test_invalid_form(self):
        data = {'image': 'wrong data'}
        form = ImageForm(files=data)

        self.assertFalse(form.is_valid())


class TestCustomUserCreationForm(TestCase):
    def test_fields_is_email(self):
        field = CustomUserCreationForm.fields
        self.assertEqual(field, ('email',))

    def test_model_is_CustomUser(self):
        model = CustomUserCreationForm._meta.model
        self.assertIsInstance(model, CustomUser)
    
    def test_valid_form(self):
        data = {'email': 'foo@foo.bar'}
        form = CustomUserCreationForm(data=data)
        self.assertTrue(form.is_valid())
    
