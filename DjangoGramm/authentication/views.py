from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect


def login_user(request):
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # message
            return redirect(request.GET.get('next', 'dj_gram:feed'))

        else:
            # Return an 'invalid login' error message.
            print('Wrong')
            pass
    else:
        return render(request, 'authentication/login.html', {'form': AuthenticationForm})


def logout_user(request):
    logout(request)
    return HttpResponse('Logget out')
