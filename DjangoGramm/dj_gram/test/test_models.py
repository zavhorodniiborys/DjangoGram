import shutil
from PIL import Image as Img
from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile, InMemoryUploadedFile
from django.test import TestCase, override_settings

from ..models import *
from .conf import TEST_DIR, create_test_image


class TestCustomUserModel(TestCase):
    @classmethod
    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='test@test.com', password='password', first_name='John',
                                              last_name='Doe', bio='Some bio')
        avatar = SimpleUploadedFile('test_image.jpg', b'some content')
        user.avatar = avatar
        user.save()

        CustomUser.objects.create_superuser(email='admin@admin.admin')
    
    def setUp(self):
        self.user = CustomUser.objects.get(email='test@test.com')
        self.superuser = CustomUser.objects.get(email='admin@admin.admin')

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
        self.assertEqual(self.user.first_name, 'John')

    def test_customuser_first_name_max_length(self):
        max_length = CustomUser._meta.get_field('first_name').max_length
        self.assertEqual(max_length, 32)

    #  testing last_name
    def test_customuser_last_name(self):
        self.assertEqual(self.user.last_name, 'Doe')

    def test_customuser_last_name_max_length(self):
        max_length = self.user._meta.get_field('last_name').max_length
        self.assertEqual(max_length, 32)

    #  testing email
    def test_customuser_email(self):
        self.assertEqual(self.user.email, 'test@test.com')

    def test_customuser_email_max_length(self):
        max_length = CustomUser._meta.get_field('email').max_length
        self.assertEqual(max_length, 255)

    def test_customuser_email_verbose_name(self):
        verbose_name = CustomUser._meta.get_field('email').verbose_name
        self.assertEqual(verbose_name, 'email address')

    def test_customuser_email_unique(self):
        #  user = CustomUser.objects.get(id=1)
        unique = CustomUser._meta.get_field('email').unique
        self.assertTrue(unique)

    #  testing password
    def test_customuser_password(self):
        self.assertEqual(self.user.check_password('password'), True)

    #  testing bio
    def test_customuser_bio(self):
        self.assertEqual(self.user.bio, 'Some bio')

    def test_customuser_bio_max_length(self):
        max_length = CustomUser._meta.get_field('bio').max_length
        self.assertEqual(max_length, 512)

    #  testing avatar
    def test_customuser_avatar(self):
        avatar_url = self.user.avatar.url
        self.assertEqual(avatar_url, '/media/images/avatars/test_image.jpg')

    #  testing user creation
    def test_customuser_create_user_default_kwargs(self):
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_active)

    def test_customuser_create_superuser_default_kwargs(self):
        self.assertTrue(self.superuser.is_superuser)
        self.assertTrue(self.superuser.is_staff)
        self.assertTrue(self.superuser.is_active)


class TestTag(TestCase):
    @classmethod
    def setUpTestData(cls):
        Tag.objects.create(name='MUST BE LOWERCASE')
    
    def setUp(self):
        self.tag = Tag.objects.get(name='must be lowercase')

    # testing name
    def test_tag_name(self):
        self.assertEqual(self.tag.name, 'must be lowercase')

    def test_tag_name_max_length(self):
        length = Tag._meta.get_field('name').max_length
        self.assertEqual(length, 32)

    def test_tag_name_unique(self):
        unique = Tag._meta.get_field('name').unique
        self.assertTrue(unique)

    #  testing save
    def test_tag_save(self):
        self.assertTrue(self.tag.name.islower())


class TestImages(TestCase):
    @classmethod
    @override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='test@test.test')
        post = Post.objects.create(user=user)

        Images.objects.create(post=post, image=create_test_image(size=(100, 100)))
    
    def setUp(self):
        self.user = CustomUser.objects.get(email='test@test.test')
        self.post = self.user.posts.first()
        self.image = self.post.images.first()

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
        image = Images.objects.create(post=self.post, image=really_big_image).image
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
        Vote.objects.create(user=user, post=post, vote=True)
    
    def setUp(self):
        self.user = CustomUser.objects.get(email='test@test.test)
        self.post = self.user.posts.first()
        self.vote = vote.objects.get(user=self.user.first())

    #  testing user
    def test_vote_user_foreign_key(self):
        user_field = Vote._meta.get_field('user')
        self.assertIsInstance(user_field, models.ForeignKey)

    def test_vote_user_is_CustomUser(self):
        self.assertIsInstance(self.vote.user, CustomUser)

    def test_vote_user_on_delete_cascade(self):
        on_delete = Vote._meta.get_field('user').remote_field.on_delete
        self.assertEqual(on_delete, models.CASCADE)

    def test_vote_user_related_name(self):
        vote = self.user.votes.first()
        self.assertIsInstance(vote, Vote)

    #  testing post
    def test_vote_post_foreign_key(self):
        post_field = Vote._meta.get_field('post')
        self.assertIsInstance(post_field, models.ForeignKey)

    def test_vote_post_is_Post(self):
        post = self.vote.post
        self.assertIsInstance(post, Post)

    def test_vote_post_on_delete_cascade(self):
        on_delete = Vote._meta.get_field('post').remote_field.on_delete
        self.assertEqual(on_delete, models.CASCADE)

    def test_vote_post_related_name(self):
        vote = self.post.votes.first()
        self.assertIsInstance(vote, Vote)

    #  testing vote
    def test_vote_boolean_field(self):
        vote_field = Vote._meta.get_field('vote')
        self.assertIsInstance(vote_field, models.BooleanField)

    #  testing Meta
    def test_vote_meta_unique_together_(self):
        unique_together = Vote._meta.unique_together[0]
        self.assertEqual(unique_together, ('user', 'post'))


class TestPost(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(email='test@test.test')
        post = Post.objects.create(user=user)

        #  creating tag for testing m2m
        post.tags.add(Tag.objects.create(name='test_tag'))

        #  creating votes for testing get_likes/dislikes functional
        Vote.objects.create(user=user, post=post, vote=True)
        Vote.objects.create(user=CustomUser.objects.create_user(email='foo@foo.foo'),
                            post=post, vote=True)
        Vote.objects.create(user=CustomUser.objects.create_user(email='bar@bar.bar'),
                            post=post, vote=False)
    
    def setUp(self):
        self.user = CustomUser.objects.get(email='test@test.test')
        post = Post.objects.get(user=self.user).first()

    #  testing Meta
    def test_post_meta_ordering(self):
        #post = Post.objects.get(id=1)
        #ordering = post._meta.ordering[0]
        ordering = Post._meta.ordering[0]
        self.assertEqual(ordering, '-id')

    #  testing user
    def test_post_user_foreign_key(self):
        user_field = Post._meta.get_field('user')
        self.assertIsInstance(user_field, models.ForeignKey)

    #def test_post_user_foreign_key_is_CustomUser(self):
    #    post = Post.objects.get(id=1)
    #    user = post.user
    #    self.assertIsInstance(user, CustomUser)

    def test_post_user_on_delete_cascade(self):
        on_delete = Post._meta.get_field('user').remote_field.on_delete
        self.assertEqual(on_delete, models.CASCADE)

    def test_post_user_related_name(self):
        post = self.user.posts.first()
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
        tag = self.post.tags.first()
        self.assertIsInstance(tag, Tag)

    def test_post_tag_blank(self):
        is_blank = Post._meta.get_field('tags').blank
        self.assertTrue(is_blank)

    def test_post_tag_related_name(self):
        tag = self.post.tags.first()
        post = tag.posts.first()

        self.assertIsInstance(post, Post)

    #  testing get_likes/get_dislikes
    def test_post_get_likes(self):
        likes_count = self.post.get_likes()
        dislikes_count = self.post.get_dislikes()

        self.assertEqual(likes_count, 2)
        self.assertEqual(dislikes_count, 1)
