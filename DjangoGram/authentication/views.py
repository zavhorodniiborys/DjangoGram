from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from authentication.forms import CustomAuthenticationForm


class LoginUser(FormView):
    form_class = CustomAuthenticationForm
    template_name = 'authentication/login.html'

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return redirect(self.request.GET.get('next', reverse('dj_gram:profile', kwargs={'pk': user.id})))

    def form_invalid(self, form):
        for field in form:
            field.field.widget.attrs['class'] += ' is-invalid'
        return super().form_invalid(form)


def logout_user(request):
    logout(request)
    return redirect(reverse('authentication:login_user'))
