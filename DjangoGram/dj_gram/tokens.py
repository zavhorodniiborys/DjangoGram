from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from .models import CustomUser


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return user.pk + timestamp + user.is_active

    def verify_token(self, uidb64, umailb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            email = force_str(urlsafe_base64_decode(umailb64))
            user = CustomUser.objects.get(pk=uid, email=email)

        except(TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user is not None and self.check_token(user, token):
            return True

        else:
            return False


account_activation_token = AccountActivationTokenGenerator()
