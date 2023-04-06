from django.contrib.auth.forms import AuthenticationForm
from django.test import TestCase

from django.urls import reverse

from ..views import LoginUser
import dj_gram.models as models


class TestLoginUser(TestCase):

    def test_anonymous_user(self):
        response = self.client.get(reverse('authentication:login_user'))
        self.assertEqual(response.status_code, 200)

    def test_form_class(self):
        form_class = LoginUser.form_class
        self.assertEqual(form_class, AuthenticationForm)

    def test_template_name(self):
        template_name = LoginUser.template_name
        self.assertEqual(template_name, 'authentication/login.html')

    def test_form_valid(self):
        models.CustomUser.objects.create_user(email='foo@foo.foo', password='Super password', is_active=True)
        data = {'username': 'foo@foo.foo', 'password': 'Super password'}
        response = self.client.get(reverse('authentication:login_user'))
        self.assertFalse(response.context['user'].is_authenticated)

        response = self.client.post(reverse('authentication:login_user'), data, follow=True)

        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('dj_gram:feed'))


class TestLogoutUser(TestCase):
    def test_logout(self):
        user = models.CustomUser.objects.create_user(email='foo@foo.foo', password='Super password', is_active=True)
        self.client.force_login(user)
        response = self.client.get(reverse('authentication:logout_user'), follow=True)

        self.assertFalse(response.context['user'].is_authenticated)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('authentication:login_user'))
