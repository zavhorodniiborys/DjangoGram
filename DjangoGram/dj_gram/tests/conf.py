from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import override_settings

TEST_DIR = 'dj_gram/tests/test_data'


def create_test_image(size=(100, 100)):
    image = Image.new('RGB', size=size)
    temp = BytesIO()
    image.save(temp, 'jpeg')
    image.close()

    temp_image = InMemoryUploadedFile(file=temp, field_name=None, name='IMAGE.jpg',
                                      content_type='image/jpeg',
                                      size=image.size, charset=None)
    return temp_image
