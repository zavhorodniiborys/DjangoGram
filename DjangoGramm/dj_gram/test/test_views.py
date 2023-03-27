import shutil

from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import *
from .conf import create_test_image, TEST_DIR


class TestIndex(TestCase):
    @classmethod
    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='foo@foo.foo', password='Super password',
                                                   first_name='John', last_name='Doe')
        post = Post.objects.create(user=user)
        image = Images.objects.create(image=create_test_image(), post=post)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DIR, ignore_errors=True)
        super().tearDownClass()

    def test_view_post(self):
        client = Client()
        print(self.client.login(email='foo@foo.foo', password='Super password'))
        response = self.client.get(reverse('dj_gram:view_post', kwargs={'post_id': 1}))
        print(response.context)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/view_post.html')
