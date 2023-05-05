from django.contrib.auth.forms import AuthenticationForm


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super(CustomAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["class"] = "form-control rounded-3"
        self.fields["username"].widget.attrs["placeholder"] = " "
        self.fields["password"].widget.attrs["class"] = "form-control rounded-3"
        self.fields["password"].widget.attrs["placeholder"] = " "
