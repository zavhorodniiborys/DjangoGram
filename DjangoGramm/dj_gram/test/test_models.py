import shutil
from PIL import Image as Img
from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
from django.test import TestCase, override_settings
from ..models import *

TEST_DIR = 'dj_gram/test/test_data'


class TestCustomUserModel(TestCase):
    @classmethod
    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='test@test.com', first_name='John', last_name='Doe', bio='Some bio')
        avatar = SimpleUploadedFile('test_image.jpg', b'some content')
        user.avatar = avatar
        user.save()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DIR, ignore_errors=True)
        super().tearDownClass()

    def test_customuser_first_name(self):
        user = CustomUser.objects.get(id=1)
        max_length = user._meta.get_field('first_name').max_length

        self.assertEqual(max_length, 32)
        self.assertEqual(user.first_name, 'John')

    def test_customuser_last_name(self):
        user = CustomUser.objects.get(id=1)
        max_length = user._meta.get_field('last_name').max_length

        self.assertEqual(max_length, 32)
        self.assertEqual(user.last_name, 'Doe')

    def test_customuser_email(self):
        user = CustomUser.objects.get(id=1)
        max_length = user._meta.get_field('email').max_length
        verbose_name = user._meta.get_field('email').verbose_name
        unique = user._meta.get_field('email').unique

        self.assertEqual(max_length, 255)
        self.assertEqual(verbose_name, 'email address')
        self.assertEqual(user.email, 'test@test.com')
        self.assertEqual(unique, True)

    def test_customuser_bio(self):
        user = CustomUser.objects.get(id=1)
        max_length = user._meta.get_field('bio').max_length

        self.assertEqual(max_length, 512)
        self.assertEqual(user.bio, 'Some bio')

    def test_customuser_avatar(self):
        user = CustomUser.objects.get(id=1)
        avatar_url = user.avatar.url
        self.assertEqual(avatar_url, '/media/images/avatars/test_image.jpg')

    def test_customuser_required(self):
        pass
    
    def test_customuser_email_is_username(self):
        pass


class TestTag(TestCase):
    @classmethod
    def setUpTestData(cls):
        Tag.objects.create(name='tag')

    def test_tag_name(self):
        tag = Tag.objects.get(id=1)
        length = tag._meta.get_field('name').max_length
        unique = tag._meta.get_field('name').unique

        self.assertEqual(length, 32)
        self.assertEqual(unique, True)
        self.assertEqual(tag.name, 'tag')

    def test_tag_validate(self):
        pass

    
class TestImages(TestCase):
    @classmethod
    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def setUpTestData(cls):
        image = SimpleUploadedFile(name='test_image.jpg', content=b'some content', content_type='image/jpeg')

        # image.close()
        # print(image)
        #  https://stackoverflow.com/questions/26298821/django-testing-model-with-imagefield
        Images.objects.create(image=image.url)


    def test_foo(self):
        pass

    # def test_image_path(self):
    #     image = Image.objects.get(id=1)
    #     image_path = image.image.url
    #
    #     self.assertEqual(image_path, '/media/images/avatars/test_image.jpg')
    #
    # def test_image_verbose_name(self):
    #     image_verbose_name = Images.Meta.verbose_name
    #     self.assertEqual(image_verbose_name, 'image')
    #
    # def test_image_verbose_name_plural(self):
    #     image_verbose_name_plural = Images.Meta.verbose_name_plural
    #     self.assertEqual(image_verbose_name_plural, 'images')
    #
    # # @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    # # def test_image_save(self):
    # #     image = Img.new('RGB', (500, 500))
    # #     image.show()
    # #     image.save()
    #
    #
    #
    # @classmethod
    # def tearDownClass(cls):
    #     shutil.rmtree(TEST_DIR, ignore_errors=True)
    #     super().tearDownClass()


class TestPost(TestCase):
    pass
