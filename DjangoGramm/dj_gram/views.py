from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import IntegrityError
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import ListView
from django.views.generic.edit import CreateView, FormView
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
    post_form = MultipleTagsForm()
    image_form = ImageForm()

    if request.method == 'POST':
        post_form = MultipleTagsForm(request.POST)
        image_form = ImageForm(request.POST, request.FILES)
        images = request.FILES.getlist('image')

        if post_form.is_valid() and image_form.is_valid():

            post_tags = post_form.cleaned_data['tag']
            post = Post.objects.create(user=request.user)

            for tag in post_tags:
                tag = Tag.objects.get(name=tag)

                if not tag:
                    tag = Tag.objects.create(name=tag)
                post.tag.add(tag)

            Images.objects.create(post=post, image=images[0])
            # image_form.save()
            # for image in images:
            #     image.save()
            #     Images.objects.create(post=post, image=image)

            return redirect(reverse('dj_gram:feed'))

    context = {'post_form': post_form, 'image_form': image_form}
    return render(request, 'dj_gram/add_post.html', context)


class AddTag(FormView):
    template_name = 'dj_gram/add_tag.html'
    form_class = TagForm

    def form_valid(self, form):
        name = form.cleaned_data['name']
        post = Post.objects.get(pk=self.kwargs['post_id'])  # maybe it`s better to check if user is the author of post
        tag = Tag.objects.filter(name=name).first()

        if not tag:
            print(name)
            tag = Tag.objects.create(name=name)

        post.tag.add(tag)
        return super(AddTag, self).form_valid(form)

    def get_success_url(self):
        return reverse('dj_gram:view_post', kwargs={'post_id': self.kwargs['post_id']})


def registration(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)  # maybe it`s better don`t attach form to model todo
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

            form = CustomUserFillForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_active = True
                user.save()

                return redirect(reverse('authentication:login'))
        else:
            form = CustomUserFillForm(request.POST)

        context = {'form': form}
        return render(request, 'dj_gram/create_profile.html', context)

    else:
        return HttpResponse('Wrong verification key')


class Feed(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'dj_gram/feed.html'

    paginate_by = 2


@login_required
def view_post(request, post_id):
    post = Post.objects.get(pk=post_id)
    return render(request, 'dj_gram/view_post.html', {'post': post})


def vote(request, post_id, vote):
    post = Post.objects.get(pk=post_id)
    try:
        Vote.objects.create(profile=request.user, post=post, vote=vote)
    except IntegrityError:
        user_vote = Vote.objects.get(post=post, profile=request.user)

        if user_vote.vote == vote:
            user_vote.delete()
        else:
            user_vote.delete()
            Vote.objects.create(profile=request.user, post=post, vote=vote)

    return redirect(request.META.get('HTTP_REFERER'))


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
