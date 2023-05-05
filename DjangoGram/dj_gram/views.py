import cloudinary
from django.conf.global_settings import EMAIL_HOST_USER
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser
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
from django.shortcuts import redirect, get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages

from .forms import *
from .tokens import account_activation_token


def index(request):
    return redirect(reverse('dj_gram:feed'), permanent=True)


class HeaderContextMixin:
    @staticmethod
    def get_header_context(user_id=None, selected_nav_elem=None, *args, **kwargs):
        context = {'nav_elements': [
            {'title': 'FEED', 'url': reverse('dj_gram:feed')},
            {'title': 'POSTS', 'url': reverse('dj_gram:feed')}],
            'selected_nav_elem': selected_nav_elem}

        if user_id is not None:
            profile_url = reverse('dj_gram:profile', kwargs={'pk': user_id})
            extra = [{'title': 'PROFILE', 'url': profile_url},
                     {'title': 'LOGOUT', 'url': reverse('authentication:logout_user')}]
        else:
            extra = [{'title': 'PROFILE', 'url': reverse('authentication:login_user')},
                     {'title': 'LOGIN', 'url': reverse('authentication:login_user')}]

        context['nav_elements'].extend(extra)

        return context


class PostContextMixin:
    def _get_voting_context(self, posts: list):
        context = {'votes': {}}
        for post in posts:
            if Vote.objects.filter(post=post.id, user=self.request.user):
                context['votes'][post.id] = Vote.objects.get(post=post.id, user=self.request.user).vote

        return context

    def _get_add_tag_context(self):
        context = {'add_tag_form': TagForm()}
        return context

    def get_post_context(self, posts: list):
        context = {}
        voting_context = self._get_voting_context(posts=posts)
        add_tag_context = self._get_add_tag_context()

        context.update(voting_context)
        context.update(add_tag_context)

        return context


class AddPost(HeaderContextMixin, LoginRequiredMixin, FormView):
    template_name = 'dj_gram/add_post.html'
    image_form = ImageForm
    multiple_tags_form = MultipleTagsForm
    success_url = reverse_lazy('dj_gram:feed')

    def get_form_class(self):
        return self.image_form

    def get_forms(self, image_form=None, multiple_tags_form=None):
        """Return an instance of the form to be used in this view."""
        if image_form is None:
            image_form = self.image_form
            multiple_tags_form = self.multiple_tags_form
        return [image_form(**self.get_form_kwargs()), multiple_tags_form(**self.get_form_kwargs())]

    def get_context_data(self, **kwargs):
        kwargs["image_form"], kwargs['multiple_tags_form'] = self.get_forms()
        header_context = self.get_header_context(self.request.user.id, selected_nav_elem="POSTS")
        kwargs.update(header_context)

        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        image_form, multiple_tags_form = self.get_forms()
        if image_form.is_valid() and multiple_tags_form.is_valid():
            return self.form_valid(image_form, multiple_tags_form)
        else:
            return self.form_invalid(image_form, multiple_tags_form)

    def form_valid(self, image_form, multiple_tags_form):
        post = Post.objects.create(user=self.request.user)
        multiple_tags_form.save(post=post)
        image_form.save(post=post)
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, image_form, multiple_tags_form):
        return self.render_to_response(self.get_context_data(image_form=image_form,
                                                             multiple_tags_form=multiple_tags_form))


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


class Registration(HeaderContextMixin, FormView):
    template_name = 'dj_gram/registration.html'
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        header_context = self.get_header_context()
        context.update(header_context)

        return context

    def get_success_url(self):
        return reverse('dj_gram:registration')


class FillProfile(HeaderContextMixin, FormView):
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
        user = form.save()
        return super(FillProfile, self).form_valid(form)

    def get_context_data(self, **kwargs):
        contex = super(FillProfile, self).get_context_data()
        header_context = self.get_header_context()

        contex.update(header_context)
        return contex

    def get_success_url(self):
        return reverse('authentication:login_user')


class ProfilePage(HeaderContextMixin, PostContextMixin, LoginRequiredMixin, ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'dj_gram/profile_page.html'
    paginate_by = 5

    def get_queryset(self):
        self.queryset = Post.objects.filter(user=CustomUser.objects.get(pk=self.kwargs['pk']))
        return super().get_queryset()

    def get_followed_context(self, showed_profile):
        user_profile = self.request.user
        followed_context = {}
        if self.request.user != showed_profile:
            try:
                Follow.objects.get(user=user_profile, followed_id=showed_profile)
                followed_context['is_followed'] = True
            except Follow.DoesNotExist:
                followed_context['is_followed'] = False
        else:
            followed_context['is_followed'] = False

        return followed_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        header_context = self.get_header_context(self.request.user.id, selected_nav_elem='PROFILE')
        context['profile'] = CustomUser.objects.get(pk=self.kwargs['pk'])
        context['pubs_count'] = Post.objects.filter(user=context['profile']).count()
        followed_context = self.get_followed_context(showed_profile=context['profile'])
        post_context = self.get_post_context(context['posts'])

        context.update(header_context)
        context.update(followed_context)
        context.update(post_context)

        return context


class EditProfilePage(HeaderContextMixin, LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        header_context = self.get_header_context(self.request.user.id, selected_nav_elem='PROFILE')
        context.update(header_context)

        return context


class Feed(HeaderContextMixin, PostContextMixin, ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'dj_gram/feed.html'
    paginate_by = 3

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        if not isinstance(self.request.user, AnonymousUser):
            post_context = self.get_post_context(context['posts'])
            context.update(post_context)

        header_context = self.get_header_context(self.request.user.id, selected_nav_elem='FEED')
        context.update(header_context)

        return context


class ViewPost(HeaderContextMixin, PostContextMixin, LoginRequiredMixin, DetailView):
    model = Post
    context_object_name = 'post'
    template_name = 'dj_gram/view_post.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        post_context = self.get_post_context([context['post']])
        header_context = self.get_header_context(self.request.user.id, selected_nav_elem='FEED')
        context.update(post_context)
        context.update(header_context)

        return context


class Voting(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        vote = bool(self.kwargs['vote'])
        post = Post.objects.get(pk=self.kwargs['post_id'])
        user_vote = Vote.objects.filter(post=post, user=self.request.user).first()

        if not user_vote:
            Vote.objects.create(user=self.request.user, post=post, vote=vote)
        else:
            if user_vote.vote == vote:
                user_vote.delete()
            else:
                user_vote.vote = vote
                user_vote.save()

        return redirect(self.request.META.get('HTTP_REFERER'))


class Subscribe(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.id != self.kwargs['followed_user_id']:
            followed_user = get_object_or_404(CustomUser, id=self.kwargs['followed_user_id'])

            if self.kwargs['action'] == 'subscribe':
                self._subscribe(request, followed_user)
            elif self.kwargs['action'] == 'unsubscribe':
                self._unsubscribe(request, followed_user)

            return redirect(request.META.get('HTTP_REFERER'))
        else:
            messages.error(request, 'Choose another account to subscribe.')

    @staticmethod
    def _subscribe(request, followed_user):
        try:
            Follow.objects.create(user=request.user, followed_id=followed_user)
            followed_user.followed_count = followed_user.followed_count + 1
            followed_user.save(update_fields=['followed_count'])
            request.user.follow_count = request.user.follow_count + 1
            request.user.save(update_fields=['follow_count'])
            messages.success(request, 'You\'ve successfully followed user.')
        except IntegrityError:
            messages.error(request, 'You\'ve already followed this user.')

    @staticmethod
    def _unsubscribe(request, followed_user):
        follow = get_object_or_404(Follow, user=request.user, followed_id=followed_user)
        follow.delete()
        followed_user.followed_count = followed_user.followed_count - 1
        followed_user.save(update_fields=['followed_count'])
        request.user.follow_count = request.user.follow_count - 1
        request.user.save(update_fields=['follow_count'])
        messages.success(request, 'You\'ve successfully unfollowed user.')
