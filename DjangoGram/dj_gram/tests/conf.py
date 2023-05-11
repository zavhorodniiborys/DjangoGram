from io import BytesIO

from PIL import Image
import cloudinary
from django.core.files.uploadedfile import InMemoryUploadedFile


def create_test_image(size=(100, 100)):
    image = Image.new('RGB', size=size)
    temp = BytesIO()
    image.save(temp, 'jpeg')
    image.close()

    temp_image = InMemoryUploadedFile(file=temp, field_name=None, name='IMAGE.jpg',
                                      content_type='image/jpeg',
                                      size=image.size, charset=None)
    return temp_image


def delete_cloudinary_images(users=None, images=None):
    if users:
        for user in users:
            if user.avatar.public_id:
                cloudinary.uploader.destroy(user.avatar.public_id, invalidate=True)

    if images:
        for image in images:
            if image.image.public_id:
                cloudinary.uploader.destroy(image.image.public_id, invalidate=True)
