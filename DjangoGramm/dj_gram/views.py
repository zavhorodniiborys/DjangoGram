from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic.edit import CreateView
from django.shortcuts import render
from django.http import HttpResponse
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site


from .models import *
from .forms import *
from .tokens import account_activation_token


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

            post_tags = post_form.cleaned_data['tag']
            post = Post.objects.create(profile=profile, tag=post_tags)

        for image in images:
            Images.objects.create(post=post, image=image)

    context = {'post_form': post_form, 'image_form': image_form}

    return render(request, 'dj_gram/add_post.html', context)


def create_registration_link(request, user):
    domain = get_current_site(request).domain
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user=user)

    return domain, uid, token


def registration(request):
    if request.method == 'POST':
        form = CustomUserRegistrationMail(request.POST)  # maybe it`s better don`t attach form to model todo
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            domain, uid, token = create_registration_link(request, user)

            # send_mail(
            #     'Email confirmation',  # subject
            #     'Your unique link',  # message
            #     'zavgorodnijboris188@gmail.com',  # from email
            #     [user.email],  # to email
            # )

            context = {
                'domain': domain,
                'uidb64': uid,
                'token': token
            }

            return render(request, 'dj_gram/activate_email.html', context)

    else:
        form = CustomUserCreationForm()

    return render(request, 'dj_gram/register.html', {'form': form})


def confirm_email(request, uidb64, token):
    if request.method == 'POST':
        form = CustomUserCreateProfile(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            # user.is_active = False

            user.save()
    else:
        activate_profile(request, uidb64, token)
        form = CustomUserCreateProfile(instance=request.user)

    context = {'form': form}
    return render(request, 'dj_gram/create_profile.html', context)



def activate_profile(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        # return redirect('home')
        return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')

def create_profile():
    pass




def feed(request):
    pass


def profile(request, profile_id):
    pass
