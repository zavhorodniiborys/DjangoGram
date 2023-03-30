import shutil

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..forms import TagForm
from ..models import *
from .conf import create_test_image, TEST_DIR
from ..views import AddTag


class TestIndex(TestCase):
    @classmethod
    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='foo@foo.foo', password='Super password',
                                              first_name='John', last_name='Doe', is_active=True)
        post = Post.objects.create(user=user)
        image = Images.objects.create(image=create_test_image(), post=post)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DIR, ignore_errors=True)
        super().tearDownClass()

    def test_view_post(self):
        #  testing access by anonymous user
        response = self.client.get(reverse('dj_gram:view_post', kwargs={'post_id': 1}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')

        #  testing access by authenticated user
        user = CustomUser.objects.get(id=1)
        self.client.force_login(user=user)
        response = self.client.get(reverse('dj_gram:view_post', kwargs={'post_id': 1}), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/view_post.html')
        self.assertIsInstance(response.context['post'], Post)
        self.assertEqual(response.context['post'].id, 1)


class TestAddTag(TestCase):
    @classmethod
    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='foo@foo.foo', password='Super password',
                                              first_name='John', last_name='Doe', is_active=True)
        post = Post.objects.create(user=user)
        image = Images.objects.create(image=create_test_image(), post=post)

    def test_anonymous_user(self):
        response = self.client.get(reverse('dj_gram:add_tag', kwargs={'post_id': 1}), follow=True)
        self.assertRedirects(response, reverse('authentication:login_user') + '?next=/post/1/add_tag')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')

    def test_template_name(self):
        template_name = AddTag.template_name
        self.assertEqual(template_name, 'dj_gram/add_tag.html')

    def test_form_class(self):
        form_class = AddTag.form_class
        self.assertEqual(form_class, TagForm)

    def test_authenticated_user_GET(self):
        user = CustomUser.objects.get(id=1)
        self.client.force_login(user=user)

        response = self.client.get(reverse('dj_gram:add_tag', kwargs={'post_id': 1}), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/add_tag.html')

    def test_authenticated_user_POST_success(self):
        post = Post.objects.get(id=1)
        user = CustomUser.objects.get(id=1)
        self.client.force_login(user=user)

        response = self.client.post(reverse('dj_gram:add_tag', kwargs={'post_id': post.id}), {'name': '#tag'},
                                    follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/view_post.html')
        self.assertEqual(post.tags.first().name, 'tag')

    def test_authenticated_user_POST_empty(self):
        post = Post.objects.get(id=1)
        user = CustomUser.objects.get(id=1)
        self.client.force_login(user=user)

        response = self.client.post(reverse('dj_gram:add_tag', kwargs={'post_id': post.id}), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/add_tag.html')
        self.assertEqual(post.tags.count(), 0)
    
    def test_authenticated_user_POST_not_valid(self):
        post = Post.objects.get(id=1)
        user = CustomUser.objects.get(id=1)
        self.client.force_login(user=user)

        response = self.client.post(reverse('dj_gram:add_tag', kwargs={'post_id': post.id}), {'name': 'wrong_tag'},
                                    follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/view_post.html')
        self.assertEqual(post.tags.first().name, 'tag')
        self.assertTrue('error: true' in response.context)
    

class Test_add_post(TestCase):
    def test_anonymous_user(self):
        response = self.client.get(reverse('dj_gram:add_post'), follow=True)
        self.assertRedirects(response, reverse('authentication:login_user') + '?next=/post/1/add_tag')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')
    
    def test_multiple_tags_form(self):
        user = CustomUser.objects.get(id=1)
        self.client.force_login(user=user)
        response = self.client.get(reverse('dj_gram:add_post'), follow=True)

        self.assertTrue('MultipleTagsForm' in response.context)

    def test_image_form(self):
        user = CustomUser.objects.get(id=1)
        self.client.force_login(user=user)
        response = self.client.get(reverse('dj_gram:add_post'), follow=True)

        self.assertTrue('MultipleTagsForm' in response.context)

    def test_authenticated_user_GET(self):
        user = CustomUser.objects.get(id=1)
        self.client.force_login(user=user)

        response = self.client.get(reverse('dj_gram:add_post'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/add_post.html')
    
    def test_authenticated_user_POST_success(self):
        user = CustomUser.objects.get(id=1)
        self.client.force_login(user=user)

        data = {'name': '#two #tags'}
        files = {'image': create_test_image()}

        response = self.client.get(reverse('dj_gram:add_post'), data=data, files=files, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/add_post.html')
        self.assertRedirects(response, 'dj_gram:feed')
        
        post = Post.objects.get(id=1)
        image = Images.objects.get(id=1)
        self.assertTrue(post.tags.count()==2)
        self.assertEqual(image.post, post)

    def test_authenticated_user_POST_fail(self):
        pass
