from django.conf.global_settings import EMAIL_HOST_USER
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages

from .forms import *
from .tokens import account_activation_token


@login_required
def add_post(request):
    multiple_tags_form = MultipleTagsForm()
    image_form = ImageForm()

    if request.method == 'POST':
        multiple_tags_form = MultipleTagsForm(request.POST)
        image_form = ImageForm(request.POST, request.FILES)

        if multiple_tags_form.is_valid() and image_form.is_valid():
            post = Post.objects.create(user=request.user)
            multiple_tags_form.save(post=post)
            image_form.save(post=post)

            return redirect(reverse('dj_gram:feed'))

    context = {'multiple_tags_form': multiple_tags_form, 'image_form': image_form}
    return render(request, 'dj_gram/add_post.html', context)


class AddTag(LoginRequiredMixin, FormView):
    template_name = 'dj_gram/add_tag.html'
    form_class = TagForm

    def form_valid(self, form):
        post = Post.objects.get(pk=self.kwargs['post_id'])  # maybe I should check if user is author of the post
        form.save(post=post)
        return super(AddTag, self).form_valid(form)

    def get_success_url(self):
        return reverse('dj_gram:view_post', kwargs={'pk': self.kwargs['post_id']})


class Registration(FormView):
    template_name = 'dj_gram/register.html'
    form_class = CustomUserCreationForm

    @staticmethod
    def _create_registration_link(request, user):
        domain = get_current_site(request).domain
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        email = urlsafe_base64_encode(force_bytes(user.email))
        token = account_activation_token.make_token(user=user)

        link = f'http://{domain}/confirm_email/{uid}/{email}/{token}'
        return link

    def _create_registration_message(self, request, user):
        registration_link = self._create_registration_link(request, user)
        context = {'registration_link': registration_link}

        return strip_tags(render_to_string('dj_gram/activate_email.html', context))

    def form_valid(self, form):
        user = form.save()

        mail_message = self._create_registration_message(self.request, user)
        send_mail(
            'Email confirmation',  # subject
            mail_message,  # message
            EMAIL_HOST_USER,  # from email
            [user.email],  # to email
        )
        
        messages.success(self.request, 'We\'ve sent the registration link to your email.')
        return super(Registration, self).form_valid(form)

    def get_success_url(self):
        return reverse('dj_gram:registration')


class FillProfile(FormView):
    template_name = 'dj_gram/create_profile.html'
    form_class = CustomUserFillForm

    def dispatch(self, request, *args, **kwargs):
        uidb64 = self.kwargs['uidb64']
        umailb64 = self.kwargs['umailb64']
        token = self.kwargs['token']

        if account_activation_token.verify_token(uidb64, umailb64, token):
            return FormView.dispatch(self, request, *args, **kwargs)
        else:
            raise Http404

    def get_form(self, form_class=form_class):
        user_pk = force_str(urlsafe_base64_decode(self.kwargs['uidb64']))
        user = get_object_or_404(CustomUser, pk=user_pk)
        return form_class(instance=user, **self.get_form_kwargs())

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        return super(FillProfile, self).form_valid(form)

    def get_success_url(self):
        return reverse('authentication:login_user')


class Feed(LoginRequiredMixin, ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'dj_gram/feed.html'

    paginate_by = 3


class ViewPost(LoginRequiredMixin, DetailView):
    model = Post
    context_object_name = 'post'
    template_name = 'dj_gram/view_post.html'


@login_required
def vote(request, post_id, vote):
    vote = bool(vote)
    post = Post.objects.get(pk=post_id)

    user_vote = Vote.objects.filter(post=post, user=request.user).first()

    if not user_vote:
        Vote.objects.create(user=request.user, post=post, vote=vote)

    else:
        if user_vote.vote == vote:
            user_vote.delete()  # maybe it will be better to mark vote as "inactive" and not delete it
        else:
            user_vote.vote = vote
            user_vote.save()

    return redirect(request.META.get('HTTP_REFERER'))
