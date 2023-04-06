from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import FormView


class LoginUser(FormView):
    form_class = AuthenticationForm
    template_name = 'authentication/login.html'

    def form_valid(self, form):
        login(self.request, form.get_user())
        return redirect(self.request.GET.get('next', 'dj_gram:feed'))


def logout_user(request):
    logout(request)
    return redirect(reverse('authentication:login_user'))
