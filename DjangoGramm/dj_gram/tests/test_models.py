from django.test import TestCase
from ..models import *


class TestCustomUserModel(TestCase):
    def setUpTestData(cls):
        CustomUser.objects.create(first_name='John', last_name='Doe')
        pass
