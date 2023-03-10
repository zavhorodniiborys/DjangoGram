from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic.edit import CreateView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site

from .models import *
from .forms import *
from .tokens import account_activation_token


def index(request):
    return HttpResponse('Home page')


@login_required
def add_post(request):
    post_form = PostForm()
    image_form = ImageForm()

    if request.method == 'POST':
        post_form = PostForm(request.POST)
        image_form = ImageForm(request.POST, request.FILES)
        images = request.FILES.getlist('image')

        if post_form.is_valid() and image_form.is_valid():
            user = CustomUser.objects.get(pk=1)

            post_tags = post_form.cleaned_data['tag']
            post = Post.objects.create(user=user, tag=post_tags)

            for image in images:
                Images.objects.create(post=post, image=image)

    context = {'post_form': post_form, 'image_form': image_form}

    return render(request, 'dj_gram/add_post.html', context)


def registration(request):
    if request.method == 'POST':
        form = CustomUserRegistrationMail(request.POST)  # maybe it`s better don`t attach form to model todo
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            domain, u_id, u_email, token = create_registration_link(request, user)

            # send_mail(
            #     'Email confirmation',  # subject
            #     'Your unique link',  # message
            #     'zavgorodnijboris188@gmail.com',  # from email
            #     [user.email],  # to email
            # )

            context = {
                'domain': domain,
                'uidb64': u_id,
                'umailb64': u_email,
                'token': token
            }

            return render(request, 'dj_gram/activate_email.html', context)

    else:
        form = CustomUserCreationForm()

    return render(request, 'dj_gram/register.html', {'form': form})


def fill_profile(request, uidb64, umailb64, token):
    if verify_token(uidb64, umailb64, token):
        if request.method == 'POST':
            user_pk = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(CustomUser, pk=user_pk)

            form = CustomUserCreateProfile(request.POST, request.FILES, instance=user)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_active = True
                user.save()

                return redirect(reverse('authentication:login'))
        else:
            form = CustomUserCreateProfile(request.POST)

        context = {'form': form}
        return render(request, 'dj_gram/create_profile.html', context)

    else:
        return HttpResponse('Wrong verification key')


def feed(request):
    return render(request, 'dj_gram/feed.html')


def create_registration_link(request, user):
    domain = get_current_site(request).domain
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    email = urlsafe_base64_encode(force_bytes(user.email))
    token = account_activation_token.make_token(user=user, )

    return domain, uid, email, token


def verify_token(uidb64, umailb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        email = force_str(urlsafe_base64_decode(umailb64))
        user = CustomUser.objects.get(pk=uid, email=email)

    except(TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        return True

    else:
        return False
