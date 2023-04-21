import cloudinary
from django.conf.global_settings import EMAIL_HOST_USER
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponseRedirect
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


class DeletePost(LoginRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('dj_gram:feed')
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['previous_page'] = request.META.get('HTTP_REFERER', '/')
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        # Set self.object before the usual form processing flow.
        # Inlined because having DeletionMixin as the first base, for
        # get_success_url(), makes leveraging super() with ProcessFormView
        # overly complex.
        self.object = self.get_object()
        if self.request.user != self.object.user:
            raise PermissionDenied()

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = self.get_object()

        images = Images.objects.filter(post=self.object)
        for image in images:
            cloudinary.uploader.destroy(image.image.public_id, invalidate=True)
        
        return super().form_valid(form)


class AddTag(LoginRequiredMixin, FormView):
    template_name = 'dj_gram/add_tag.html'
    form_class = TagForm

    def post(self, request, *args, **kwargs):
        post = Post.objects.get(pk=self.kwargs['post_id'])
        user = self.request.user
        if user == post.user:
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form, post)
            else:
                return self.form_invalid(form)
        else:
            self.request.GET = None
            return redirect('authentication:logout_user')

    def form_valid(self, form, post):
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
            subject='Email confirmation',
            message=mail_message,
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email]
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


class ProfilePage(DetailView):
    model = CustomUser
    context_object_name = 'profile'
    template_name = 'dj_gram/profile_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.id != context['profile']:
            try:
                Follow.objects.get(user=self.request.user, followed_id=context['profile'])
                context['is_followed'] = True
            except Follow.DoesNotExist:
                context['is_followed'] = False
        else:
            context['is_followed'] = False
        return context


class EditProfilePage(UpdateView):
    model = CustomUser
    fields = ['first_name', 'last_name', 'bio', 'avatar']
    template_name = 'dj_gram/edit_profile_page.html'
    success_url = reverse_lazy('dj_gram:feed')

    def get(self, request, *args, **kwargs):
        if request.user.id != self.kwargs['pk']:
            raise PermissionDenied()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.user.id != self.kwargs['pk']:
            raise PermissionDenied()
        return super().post(request, *args, **kwargs)


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
            user_vote.delete()
        else:
            user_vote.vote = vote
            user_vote.save()

    return redirect(request.META.get('HTTP_REFERER'))


class Subscribe(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.id != self.kwargs['followed_user_id']:
            followed_user = get_object_or_404(CustomUser, id=self.kwargs['followed_user_id'])

            if self.kwargs['action'] == 'subscribe':
                self.subscribe(request, followed_user)
            elif self.kwargs['action'] == 'unsubscribe':
                self.unsubscribe(request, followed_user)

            return redirect(request.META.get('HTTP_REFERER'))
        else:
            messages.error(request, 'Choose another account to subscribe.')

    @staticmethod
    def subscribe(request, followed_user):
        try:
            Follow.objects.create(user=request.user, followed_id=followed_user)
            followed_user.followed_count = followed_user.followed_count + 1
            followed_user.save()
            request.user.follow_count = request.user.follow_count + 1
            request.user.save()
            messages.success(request, 'You\'ve successfully followed user.')
        except IntegrityError:
            messages.error(request, 'You\'ve already followed this user.')

    @staticmethod
    def unsubscribe(request, followed_user):
        follow = get_object_or_404(Follow, user=request.user, followed_id=followed_user)
        follow.delete()
        followed_user.followed_count = followed_user.followed_count - 1
        followed_user.save()
        request.user.follow_count = request.user.follow_count - 1
        request.user.save()
        messages.success(request, 'You\'ve successfully unfollowed user.')
