from django.test import TestCase
from ..models import *


class TestCustomUserModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        self.user = CustomUser.objects.create_user(first_name='John', last_name='Doe', email='test@test.com', bio='Some bio')
        self.user.avatar = SimpleUploadedFile(name='test_image.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg')
        self.user.save()

    def test_customuser_first_name(self):
        max_lenght = self.user._meta.get_field('first_name').max_lenght

        self.assertEqual(max_lenght, 32)
        self.assertEqual(self.user.first_name, 'John')
    
    def test_customuser_last_name(self):
        max_lenght = self.user._meta.get_field('last_name').max_lenght

        self.assertEqual(max_lenght, 32)
        self.assertEqual(self.user.last_name, 'Doe')
    
    def test_customuser_email(self):
        max_lenght = self.user._meta.get_field('email').max_lenght
        verbose_name = self.user._meta.get_field('email').verbose_name
        unique = self.user._meta.get_field('email').unique

        self.assertEqual(max_lenght, 255)
        self.assertEqual(verbose_name, 'email address')
        self.assertEqual(self.user.email, 'test@test.com')
        self.assertEqual(unique, True)
    
    def test_customuser_bio(self):
        max_lenght = self.user._meta.get_field('bio').max_lenght
        
        self.assertEqual(max_lenght, 512)
        self.assertEqual(self.user.bio, 'Doe')
    
    def test_customuser_avatar(self):
        pass

    def test_customuser_required(self):
        pass
    
    def test_customuser_email_is_username(self):
        pass


class TestTag(TestCase):
    @classmethod
    def setUpTestData(cls):
        tag_name = 'tag'
        self.tag = Tag.objects.create(name=tag_name)

    def test_tag_name(self):
        lenght = self.tag._meta.get_field('name').lenght
        unique = self.tag._meta.get_field('name').unique

        self.assertEqual(lenght, 32)
        self.assertEqual(unique, True)
        self.assertEqual(self.tag.name, tag_name)
    
    def test_tag_validate(self):
        pass

    
class TestImages(TestCase):
    @classmethod   
    def setUpTestData(cls):
        image = SimpleUploadedFile(name='test_image.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg')
        #  https://stackoverflow.com/questions/26298821/django-testing-model-with-imagefield 
        self.tag = Tag.objects.create(name=tag_name) 

