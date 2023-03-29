import shutil
from PIL import Image as Img
from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile, InMemoryUploadedFile
from django.test import TestCase, override_settings

from ..models import *
from .conf import create_test_image

TEST_DIR = 'dj_gram/test/test_data'


class TestCustomUserModel(TestCase):
    @classmethod
    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='test@test.com', password='password', first_name='John',
                                              last_name='Doe', bio='Some bio')
        avatar = SimpleUploadedFile('test_image.jpg', b'some content')
        user.avatar = avatar
        user.save()

        superuser = CustomUser.objects.create_superuser(email='admin@admin.admin')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DIR, ignore_errors=True)
        super().tearDownClass()

    #  testing settings
    def test_customuser_username_field(self):
        username_field = CustomUser.USERNAME_FIELD
        self.assertEqual(username_field, 'email')

    def test_customuser_required_fields(self):
        required_field = CustomUser.REQUIRED_FIELDS
        expected_red = []
        self.assertEqual(required_field, expected_red)

    #  testing first_name
    def test_customuser_first_name(self):
        user = CustomUser.objects.get(id=1)
        self.assertEqual(user.first_name, 'John')

    def test_customuser_first_name_max_length(self):
        max_length = CustomUser._meta.get_field('first_name').max_length
        self.assertEqual(max_length, 32)

    #  testing last_name
    def test_customuser_last_name(self):
        user = CustomUser.objects.get(id=1)
        self.assertEqual(user.last_name, 'Doe')

    def test_customuser_last_name_max_length(self):
        user = CustomUser.objects.get(id=1)
        max_length = user._meta.get_field('last_name').max_length
        self.assertEqual(max_length, 32)

    #  testing email
    def test_customuser_email(self):
        user = CustomUser.objects.get(id=1)
        self.assertEqual(user.email, 'test@test.com')

    def test_customuser_email_max_length(self):
        max_length = CustomUser._meta.get_field('email').max_length
        self.assertEqual(max_length, 255)

    def test_customuser_email_verbose_name(self):
        user = CustomUser.objects.get(id=1)
        verbose_name = CustomUser._meta.get_field('email').verbose_name
        self.assertEqual(verbose_name, 'email address')

    def test_customuser_email_unique(self):
        user = CustomUser.objects.get(id=1)
        unique = user._meta.get_field('email').unique
        self.assertTrue(unique)

    #  testing password
    def test_customuser_password(self):
        user = CustomUser.objects.get(id=1)

        self.assertEqual(user.check_password('password'), True)

    #  testing bio
    def test_customuser_bio(self):
        user = CustomUser.objects.get(id=1)
        self.assertEqual(user.bio, 'Some bio')

    def test_customuser_bio_max_length(self):
        max_length = CustomUser._meta.get_field('bio').max_length
        self.assertEqual(max_length, 512)

    #  testing avatar
    def test_customuser_avatar(self):
        user = CustomUser.objects.get(id=1)
        avatar_url = user.avatar.url
        self.assertEqual(avatar_url, '/media/images/avatars/test_image.jpg')

    #  testing user creation
    def test_customuser_create_user(self):
        user = CustomUser.objects.get(id=1)

        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_active)

    def test_customuser_create_superuser(self):
        superuser = CustomUser.objects.get(id=2)

        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_active)


class TestTag(TestCase):
    @classmethod
    def setUpTestData(cls):
        Tag.objects.create(name='MUST BE LOWERCASE')

    # testing name
    def test_tag_name(self):
        tag = Tag.objects.get(id=1)
        self.assertEqual(tag.name, 'must be lowercase')

    def test_tag_name_max_length(self):
        tag = Tag.objects.get(id=1)
        length = tag._meta.get_field('name').max_length
        self.assertEqual(length, 32)

    def test_tag_name_unique(self):
        tag = Tag.objects.get(id=1)
        unique = tag._meta.get_field('name').unique
        self.assertTrue(unique)

    #  testing save
    def test_tag_save(self):
        tag = Tag.objects.get(id=1)
        self.assertFalse(tag.name.isupper())


class TestImages(TestCase):
    @classmethod
    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='test@test.test')
        post = Post.objects.create(user=user)

        Images.objects.create(post=post, image=create_test_image(size=(100, 100)))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DIR, ignore_errors=True)
        super().tearDownClass()

    def test_image_path(self):
        image_path = Images.objects.get(id=1).image.url
        self.assertEqual(image_path, '/media/images/post/1/IMAGE.jpg')

    def test_image_verbose_name(self):
        image_verbose_name = Images._meta.verbose_name
        self.assertEqual(image_verbose_name, 'image')

    def test_image_verbose_name_plural(self):
        image_verbose_name_plural = Images._meta.verbose_name_plural
        self.assertEqual(image_verbose_name_plural, 'images')

    #  testing save
    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def test_image_create_thumbnail(self):
        really_big_image = create_test_image((2000, 1500))
        post = Post.objects.get(id=1)
        image = Images.objects.create(post=post, image=really_big_image).image
        image_thumbnail_size = image.width, image.height

        self.assertEqual(image_thumbnail_size, (960, 720))
    
    # def test_count_images_in_post(self):
    #     post = Post.objects.get(id=1)
    #     for _ in range(8):
    #         Images.objects.create(post=post, image=create_test_image(size=(100, 100)))
    #
    #     with self.assertRaises(ValidationError):
    #         image = Images(post=post, image=create_test_image(size=(100, 100)))
    #         image.save()


class TestVote(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='test@test.test')
        post = Post.objects.create(user=user)
        Vote.objects.create(profile=user, post=post, vote=True)

    #  testing profile
    def test_vote_profile_foreign_key(self):
        profile_field = Vote._meta.get_field('profile')
        self.assertIsInstance(profile_field, models.ForeignKey)

    def test_vote_profile_is_CustomUser(self):
        vote = Vote.objects.get(pk=1)
        profile = vote.profile
        self.assertIsInstance(profile, CustomUser)

    def test_vote_profile_on_delete_cascade(self):
        on_delete = Vote._meta.get_field('profile').remote_field.on_delete
        self.assertEqual(on_delete, models.CASCADE)

    def test_vote_profile_related_name(self):
        user = CustomUser.objects.get(id=1)
        related_name = user.votes.get(id=1)
        self.assertIsInstance(related_name, Vote)

    #  testing post
    def test_vote_post_foreign_key(self):
        post_field = Vote._meta.get_field('post')
        self.assertIsInstance(post_field, models.ForeignKey)

    def test_vote_post_is_Post(self):
        vote = Vote.objects.get(pk=1)
        post = vote.post
        self.assertIsInstance(post, Post)

    def test_vote_post_on_delete_cascade(self):
        on_delete = Vote._meta.get_field('post').remote_field.on_delete
        self.assertEqual(on_delete, models.CASCADE)

    def test_vote_post_related_name(self):
        post = Post.objects.get(id=1)
        related_name = post.votes.get(id=1)
        self.assertIsInstance(related_name, Vote)

    #  testing vote
    def test_vote_boolean_field(self):
        vote_field = Vote._meta.get_field('vote')
        self.assertIsInstance(vote_field, models.BooleanField)

    #  testing Meta
    def test_vote_meta_unique_together_(self):
        unique_together = Vote._meta.unique_together[0]
        self.assertEqual(unique_together, ('profile_id', 'post_id'))


class TestPost(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='test@test.test')
        post = Post.objects.create(user=user)

        #  creating tag for testing m2m
        post.tags.add(Tag.objects.create(name='test_tag'))

        #  creating votes for testing get_likes/dislikes functional
        Vote.objects.create(profile=user, post=post, vote=True)
        Vote.objects.create(profile=CustomUser.objects.create_user(email='foo@foo.foo'),
                            post=post, vote=True)
        Vote.objects.create(profile=CustomUser.objects.create_user(email='bar@bar.bar'),
                            post=post, vote=False)

    #  testing Meta
    def test_post_meta_ordering(self):
        post = Post.objects.get(id=1)
        ordering = post._meta.ordering[0]
        self.assertEqual(ordering, '-id')

    #  testing user
    def test_post_user_foreign_key(self):
        user_field = Post._meta.get_field('user')
        self.assertIsInstance(user_field, models.ForeignKey)

    def test_post_user_foreign_key_is_CustomUser(self):
        post = Post.objects.get(id=1)
        user = post.user
        self.assertIsInstance(user, CustomUser)

    def test_post_user_on_delete_cascade(self):
        on_delete = Post._meta.get_field('user').remote_field.on_delete
        self.assertEqual(on_delete, models.CASCADE)

    def test_post_user_related_name(self):
        user = CustomUser.objects.get(id=1)
        post = user.posts.get(id=1)
        self.assertIsInstance(post, Post)

    #  testing date
    def test_post_date(self):
        is_add_auto_now = Post._meta.get_field('date').auto_now_add
        self.assertTrue(is_add_auto_now)

    #  testing tag
    def test_post_tag_m2m(self):
        tag_field = Post._meta.get_field('tags')
        self.assertIsInstance(tag_field, models.ManyToManyField)

    def test_post_tag_m2m_is_Tag(self):
        post = Post.objects.get(id=1)
        tag = post.tags.first()
        self.assertIsInstance(tag, Tag)

    def test_post_tag_blank(self):
        is_blank = Post._meta.get_field('tags').blank
        self.assertTrue(is_blank)

    def test_post_tag_related_name(self):
        post = Post.objects.get(id=1)
        tag = post.tags.first()
        post = tag.posts.first()

        self.assertIsInstance(post, Post)

    #  testing get_likes/get_dislikes
    def test_post_get_likes(self):
        post = Post.objects.get(id=1)
        likes_count = post.get_likes()
        dislikes_count = post.get_dislikes()

        self.assertEqual(likes_count, 2)
        self.assertEqual(dislikes_count, 1)
