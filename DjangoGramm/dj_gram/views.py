from django.views.generic.edit import CreateView
from django.shortcuts import render
from django.http import HttpResponse

from .models import *
from .forms import *


def index(request):
    return HttpResponse('Home page')


def add_post(request):
    post_form = PostForm()
    image_form = ImageForm()

    if request.method == 'POST':
        post_form = PostForm(request.POST)
        image_form = ImageForm(request.POST, request.FILES)
        images = request.FILES.getlist('image')

        if post_form.is_valid() and image_form.is_valid():

            profile = Profile.objects.get(pk=1)
            print(profile)

            post_tags = post_form.cleaned_data['tag']
            post = Post.objects.create(profile=profile, tag=post_tags)
            print(post)

        for image in images:
            Images.objects.create(post=post, image=image)

    context = {'post_form': post_form, 'image_form': image_form}

    return render(request, 'dj_gram/add_post.html', context)


class Register(CreateView):
    model = User
    fields = ['mail', 'pass_hash']
    template_name = 'dj_gram/register.html'
def feed(request):
    pass


def profile(request, profile_id):
    pass

