from unittest.mock import patch

from django.contrib.sites.shortcuts import get_current_site
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode

from dj_gram.forms import TagForm, CustomUserCreationForm, CustomUserFillForm
from dj_gram.models import *
from .conf import create_test_image
from dj_gram.tokens import account_activation_token
from dj_gram.views import AddTag, Feed, Registration, FillProfile, ViewPost, Voting, Subscribe, AddPost,\
    LoginRequiredMixin, PostContextMixin, HeaderContextMixin


class TestViewPost(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='foo@foo.foo', password='Super password',
                                              first_name='John', last_name='Doe', is_active=True)
        post = Post.objects.create(user=user)
        image = Images.objects.create(image=create_test_image(), post=post)

    def setUp(self):
        self.user = CustomUser.objects.get(email='foo@foo.foo')
        self.post = Post.objects.get(user=self.user)

    def test_view_post(self):
        #  testing access by anonymous user
        response = self.client.get(reverse('dj_gram:view_post', kwargs={'pk': self.post.id}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')

        #  testing access by authenticated user
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('dj_gram:view_post', kwargs={'pk': self.post.id}), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/post.html')
        self.assertIsInstance(response.context['post'], Post)
        self.assertEqual(response.context['post'].id, self.post.id)

    def test_mixins_is_present(self):
        mixins = (HeaderContextMixin, PostContextMixin, LoginRequiredMixin)
        for mixin in mixins:
            with self.subTest():
                self.assertTrue(mixin in ViewPost.__bases__)


class TestAddTag(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='foo@foo.foo', password='Super password',
                                              first_name='John', last_name='Doe', is_active=True)
        post = Post.objects.create(user=user)
        image = Images.objects.create(image=create_test_image(), post=post)

    def setUp(self):
        self.user = CustomUser.objects.get(email='foo@foo.foo')
        self.post = Post.objects.first()

    def test_mixins_is_present(self):
        mixins = (LoginRequiredMixin,)
        for mixin in mixins:
            with self.subTest(mixin=mixin):
                self.assertTrue(mixin in AddTag.__bases__)

    def test_anonymous_user(self):
        response = self.client.get(reverse('dj_gram:add_tag', kwargs={'post_id': self.post.id}), follow=True)
        self.assertRedirects(response, reverse('authentication:login_user') + f'?next=/post/{self.post.id}/add_tag')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')

    def test_template_name(self):
        template_name = AddTag.template_name
        self.assertEqual(template_name, 'dj_gram/add_tag.html')

    def test_form_class(self):
        form_class = AddTag.form_class
        self.assertEqual(form_class, TagForm)

    def test_authenticated_user_GET(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('dj_gram:add_tag', kwargs={'post_id': 1}), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/add_tag.html')

    def test_authenticated_user_not_post_author_POST(self):
        user = CustomUser.objects.create_user(email='bar@bar.bar', is_active=True)
        self.client.force_login(user=user)
        response = self.client.post(reverse('dj_gram:add_tag', kwargs={'post_id': self.post.id}), {'name': '#tag'},
                                    follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('authentication:login_user'))
        self.assertFalse(self.post.tags.exists())

    def test_authenticated_user_POST_success(self):
        self.client.force_login(user=self.user)
        response = self.client.post(reverse('dj_gram:add_tag', kwargs={'post_id': self.post.id}), {'name': '#tag'},
                                    follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/post.html')
        self.assertEqual(self.post.tags.first().name, 'tag')

    def test_authenticated_user_POST_empty(self):
        self.client.force_login(user=self.user)

        response = self.client.post(reverse('dj_gram:add_tag', kwargs={'post_id': self.post.id}), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/add_tag.html')
        self.assertEqual(self.post.tags.count(), 0)


class TestAddPost(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='foo@foo.foo', password='Super password',
                                              first_name='John', last_name='Doe', is_active=True)

    def setUp(self):
        self.user = CustomUser.objects.get(email='foo@foo.foo')

    def test_mixins_is_present(self):
        mixins = (HeaderContextMixin, LoginRequiredMixin)
        for mixin in mixins:
            with self.subTest():
                self.assertTrue(mixin in AddPost.__bases__)

    def test_anonymous_user(self):
        response = self.client.get(reverse('dj_gram:add_post'), follow=True)
        self.assertRedirects(response, reverse('authentication:login_user') + '?next=/add_post/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')

    def test_multiple_tags_form(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('dj_gram:add_post'))

        self.assertIn('multiple_tags_form', response.context)

    def test_image_form(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('dj_gram:add_post'))

        self.assertTrue('image_form' in response.context)

    def test_authenticated_user_GET(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('dj_gram:add_post'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/add_post.html')

    def test_authenticated_user_POST_success(self):
        self.client.force_login(user=self.user)
        data = {'name': '#two #tags'}
        files = {'image': create_test_image().open()}
        response = self.client.post(reverse('dj_gram:add_post'), {**data, **files})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dj_gram:feed'))

        post = Post.objects.first()
        image = Images.objects.first()
        self.assertEqual(post.tags.count(), 2)
        self.assertEqual(image.post, post)


class TestFeed(TestCase):
    def test_mixins_is_present(self):
        mixins = (HeaderContextMixin, PostContextMixin)
        for mixin in mixins:
            with self.subTest():
                self.assertTrue(mixin in Feed.__bases__)

    def test_anonymous_user(self):
        response = self.client.get(reverse('dj_gram:feed'))
        self.assertEqual(response.status_code, 200)

    def test_model_is_Post(self):
        model = Feed.model
        self.assertEqual(model, Post)

    def test_context_object_name(self):
        context_object_name = Feed.context_object_name
        self.assertEqual(context_object_name, 'posts')

    def test_template_name(self):
        template_name = Feed.template_name
        self.assertEqual(template_name, 'dj_gram/feed.html')

    def test_pagination(self):
        paginate_by = Feed.paginate_by
        self.assertEqual(paginate_by, 3)


class TestVote(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='foo@foo.foo', password='Super password',
                                              first_name='John', last_name='Doe', is_active=True)
        post = Post.objects.create(user=user)

    def setUp(self) -> None:
        self.user = CustomUser.objects.get(email='foo@foo.foo')
        self.post = Post.objects.get(user=self.user)

    def test_mixins_is_present(self):
        mixins = (LoginRequiredMixin,)
        for mixin in mixins:
            with self.subTest():
                self.assertTrue(mixin in Voting.__bases__)

    def test_anonymous_user(self):
        response = self.client.get(reverse('dj_gram:vote', kwargs={'post_id': self.post.id, 'vote': 1}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('authentication:login_user') + f'?next=/post/{self.post.id}/vote/1')

    def test_create_vote_like(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dj_gram:vote', kwargs={'post_id': self.post.id, 'vote': 1}),
                                   HTTP_REFERER=reverse('dj_gram:feed'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dj_gram:feed'))

        vote = Vote.objects.get(post=self.post, user=self.user)
        self.assertTrue(vote.vote)

    def test_create_vote_dislike(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dj_gram:vote', kwargs={'post_id': self.post.id, 'vote': 0}),
                                   HTTP_REFERER=reverse('dj_gram:feed'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dj_gram:feed'))

        vote = Vote.objects.get(post=self.post, user=self.user)
        self.assertFalse(vote.vote)

    def test_change_vote(self):
        Vote.objects.create(user=self.user, post=self.post, vote=True)
        self.client.force_login(self.user)

        response = self.client.get(reverse('dj_gram:vote', kwargs={'post_id': self.post.id, 'vote': 0}),
                                   HTTP_REFERER=reverse('dj_gram:feed'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dj_gram:feed'))
        vote = Vote.objects.get(user=self.user, post=self.post)
        self.assertFalse(vote.vote)

    def test_delete_vote(self):
        Vote.objects.create(user=self.user, post=self.post, vote=True)
        self.client.force_login(self.user)

        response = self.client.get(reverse('dj_gram:vote', kwargs={'post_id': self.post.id, 'vote': 1}),
                                   HTTP_REFERER=reverse('dj_gram:feed'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dj_gram:feed'))
        with self.assertRaises(ObjectDoesNotExist):
            Vote.objects.get(user=self.user, post=self.post)


class TestRegistration(TestCase):
    def test_mixins_is_present(self):
        mixins = (HeaderContextMixin,)
        for mixin in mixins:
            with self.subTest():
                self.assertTrue(mixin in Registration.__bases__)

    def test_anonymous_user(self):
        response = self.client.get(reverse('dj_gram:registration'))
        self.assertEqual(response.status_code, 200)

    def test_template_name(self):
        template_name = Registration.template_name
        self.assertEqual(template_name, 'dj_gram/registration.html')

    def test_form_class(self):
        form_class = Registration.form_class
        self.assertEqual(form_class, CustomUserCreationForm)

    def test_create_registration_link(self):
        """Receiving request by calling GET, than uses request to create registration_link"""

        user = CustomUser.objects.create_user(email='foo@foo.bar', is_active=False)
        response = self.client.get(reverse('dj_gram:registration'))
        link = Registration()._create_registration_link(response.context['request'], user)

        domain = get_current_site(response.context['request']).domain
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        email = urlsafe_base64_encode(force_bytes(user.email))
        token = account_activation_token.make_token(user=user)
        expected_link = f'http://{domain}/confirm_email/{uid}/{email}/{token}'

        self.assertEqual(link, expected_link)

    @patch('dj_gram.views.Registration._create_registration_link', return_value='tests')
    def test_create_registration_message(self, patcher):
        """
        Registration message is the template filled with registration_link.
        Method uses patching to mock _create_registration_link as we don't need real registation link
        and only tests template creation.
        """

        user = CustomUser.objects.create_user(email='foo@foo.bar', is_active=False)
        response = self.client.get(reverse('dj_gram:registration'))
        res = Registration()._create_registration_message(response.context['request'], user)

        expected_context = {'registration_link': 'tests'}
        expected_res = strip_tags(render_to_string('dj_gram/activate_email.html', expected_context))

        self.assertEqual(res, expected_res)

    def test_form_valid(self):
        data = {'email': 'foo@foo.foo'}
        response = self.client.post(reverse('dj_gram:registration'), data=data)
        self.assertEqual(len(mail.outbox), 1)


class TestFillProfile(TestCase):
    def test_mixins_is_present(self):
        mixins = (HeaderContextMixin,)
        for mixin in mixins:
            with self.subTest():
                self.assertTrue(mixin in FillProfile.__bases__)

    def test_anonymous_user(self):
        user = CustomUser.objects.create_user(email='foo@foo.foo')
        data = {
            'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
            'umailb64': urlsafe_base64_encode(force_bytes(user.email)),
            'token': account_activation_token.make_token(user=user)
        }
        response = self.client.get(reverse('dj_gram:fill_profile', kwargs=data))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/create_profile.html')

    def test_template_name(self):
        template_name = FillProfile.template_name
        self.assertEqual(template_name, 'dj_gram/create_profile.html')

    def test_form_class(self):
        form_class = FillProfile.form_class
        self.assertEqual(form_class, CustomUserFillForm)

    def test_dispatch(self):
        user = CustomUser.objects.create_user(email='foo@foo.foo')
        data = {
            'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
            'umailb64': urlsafe_base64_encode(force_bytes(user.email)),
            'token': account_activation_token.make_token(user=user)
        }
        response = self.client.get(reverse('dj_gram:fill_profile', kwargs=data))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dj_gram/create_profile.html')

    def test_dispatch_404(self):
        data = {
            'uidb64': 'wrong uidb64',
            'umailb64': 'wrong umailb64',
            'token': 'wrong token'
        }
        response = self.client.get(reverse('dj_gram:fill_profile', kwargs=data))

        self.assertEqual(response.status_code, 404)

    def test_form_valid(self):
        user = CustomUser.objects.create_user(email='foo@foo.foo', is_active=False)
        kwargs = {
            'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
            'umailb64': urlsafe_base64_encode(force_bytes(user.email)),
            'token': account_activation_token.make_token(user=user)
        }
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'bio': 'bio',
            'password1': 'Superpassword',
            'password2': 'Superpassword',
            'avatar': create_test_image().open()
        }

        response = self.client.post(reverse('dj_gram:fill_profile', kwargs=kwargs), data)
        user = CustomUser.objects.get(email='foo@foo.foo')

        self.assertTrue(user.is_active)
        self.assertEqual(response.url, reverse('authentication:login_user'))
        self.assertEqual(user.first_name, data['first_name'])  # check if instance=user in get_form()


class TestSubscribe(TestCase):
    @classmethod
    def setUpTestData(cls):
        CustomUser.objects.create_user(email='foo@foo.foo', is_active=True)
        CustomUser.objects.create_user(email='bar@bar.bar', is_active=True)

    def setUp(self) -> None:
        self.user_1 = CustomUser.objects.get(email='foo@foo.foo')
        self.user_2 = CustomUser.objects.get(email='bar@bar.bar')

    def test_mixins_is_present(self):
        mixins = (LoginRequiredMixin,)
        for mixin in mixins:
            with self.subTest():
                self.assertTrue(mixin in Subscribe.__bases__)

    def test_subscribe(self):
        self.client.force_login(user=self.user_1)
        response = self.client.get(reverse('dj_gram:subscribe',
                                           kwargs={'followed_user_id': self.user_2.id, 'action': 'subscribe'}),
                                   HTTP_REFERER=reverse('dj_gram:feed'))

        follow_inst = Follow.objects.get(user=self.user_1, followed_id=self.user_2)
        self.assertTrue(follow_inst)

        self.user_1 = CustomUser.objects.get(email='foo@foo.foo')
        self.user_2 = CustomUser.objects.get(email='bar@bar.bar')
        self.assertEqual(self.user_1.follow_count, 1)
        self.assertEqual(self.user_2.followed_count, 1)

    def test_unsubscribe(self):
        self.client.force_login(user=self.user_1)
        response = self.client.get(reverse('dj_gram:subscribe',
                                           kwargs={'followed_user_id': self.user_2.id, 'action': 'unsubscribe'}),
                                   HTTP_REFERER=reverse('dj_gram:feed'))

        follow_inst = Follow.objects.filter(user=self.user_1, followed_id=self.user_2).first()
        self.assertFalse(follow_inst)

        self.user_1 = CustomUser.objects.get(email='foo@foo.foo')
        self.user_2 = CustomUser.objects.get(email='bar@bar.bar')
        self.assertEqual(self.user_1.follow_count, 0)
        self.assertEqual(self.user_2.followed_count, 0)
