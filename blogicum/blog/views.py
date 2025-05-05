from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView, FormView
)

from .forms import CommentForm, CreatePostForm, ProfileForm
from .models import Category, Comment, Post


User = get_user_model()


class PublishedPostMixin:
    paginate_by = 10

    def get_published_posts(self, posts=Post.objects):
        return (
            posts.select_related('location', 'category', 'author')
            .prefetch_related('comments')
            .filter(
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()
            )
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date')
        )

    def get_users_posts(self, posts=Post.objects):
        return (
            posts.select_related('location', 'category', 'author')
            .prefetch_related('comments')
            .filter(
                (Q(is_published=True)
                 & Q(category__is_published=True)
                 & Q(pub_date__lte=timezone.now()))
                | Q(author=self.request.user.id)
            )
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date')
        )


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class PostActionMixin:
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})


class Index(PublishedPostMixin, ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        return self.get_published_posts()


class PostDetail(PublishedPostMixin, FormView, DetailView):
    model = Post
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'
    form_class = CommentForm

    def get_object(self, queryset=None):
        return get_object_or_404(self.get_users_posts(),
                                 id=self.kwargs['post_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = (
            Comment.objects
            .select_related('author', 'post')
            .filter(post=self.kwargs['post_id'])
        )
        print(context)
        context['form'] = self.get_form()
        return context


class CategoryPosts(PublishedPostMixin, DetailView):
    model = Category
    context_object_name = 'category'
    template_name = 'blog/category.html'
    slug_url_kwarg = 'category_slug'
    slug_field = 'slug'

    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.get_published_posts(context['category'].posts)
        paginator = Paginator(posts, self.paginate_by)
        context['page_obj'] = paginator.get_page(self.request.GET.get('page'))
        return context


class CreatePost(LoginRequiredMixin, PostActionMixin, CreateView):
    form_class = CreatePostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class EditPost(LoginRequiredMixin, OnlyAuthorMixin,
               PostActionMixin, UpdateView):
    form_class = CreatePostForm

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs['post_id'])
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.id)
        return super().dispatch(request, *args, **kwargs)


class DeletePost(LoginRequiredMixin, OnlyAuthorMixin,
                 PostActionMixin, DeleteView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CreatePostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})


class CreateComment(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['text']

    def dispatch(self, request, *args, **kwargs):
        self.chosen_post = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.chosen_post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})


class EditComment(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'


class DeleteComment(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.object.post_id})


class Profile(PublishedPostMixin, DetailView):
    model = User
    context_object_name = 'profile'
    slug_url_kwarg = 'username'
    slug_field = 'username'
    template_name = 'blog/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.get_users_posts().filter(author=self.object)
        paginator = Paginator(posts, 10)
        context['page_obj'] = paginator.get_page(self.request.GET.get('page'))
        return context


class EditProfile(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'
    success_url = reverse_lazy('blog:profile')

    def get_object(self, queryset=None):
        print()
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})
