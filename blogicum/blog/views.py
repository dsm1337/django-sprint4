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
from .models import Category, Comment, Post, User


PAGINATE_BY = 10


def create_paginator(posts, page):
    paginator = Paginator(posts, PAGINATE_BY)
    return paginator.get_page(page)


def get_published_posts(posts=Post.objects, select_related=True,
                        published_check=True, add_comment=True, for_user=None):
    filter = Q(is_published=True, category__is_published=True,
               pub_date__lte=timezone.now())
    if select_related:
        posts = posts.select_related('location', 'category', 'author')
    if published_check:
        posts = posts.filter(filter)
    elif for_user:
        posts = posts.filter(filter | Q(author=for_user))
    if add_comment:
        posts = posts.annotate(comment_count=Count('comments'))
    return posts.order_by('-pub_date')


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        return self.get_object().author == self.request.user


class PostActionMixin:
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


class Index(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = PAGINATE_BY

    def get_queryset(self):
        return get_published_posts()


class PostDetail(FormView, DetailView):
    model = Post
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'
    form_class = CommentForm

    def get_object(self, queryset=None):
        post = super().get_object()
        if self.request.user != post.author:
            return get_object_or_404(get_published_posts(
                add_comment=False), id=post.id)
        return post

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            comments=(self.object.comments.select_related('author')),
            form=self.get_form()
        )


class CategoryPosts(DetailView):
    model = Category
    context_object_name = 'category'
    template_name = 'blog/category.html'
    slug_url_kwarg = 'category_slug'
    slug_field = 'slug'

    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)

    def get_context_data(self, **kwargs):
        category_posts = super().get_context_data()['category'].posts
        return super().get_context_data(
            **kwargs,
            page_obj=create_paginator(
                get_published_posts(category_posts),
                self.request.GET.get('page')
            )
        )


class CreatePost(LoginRequiredMixin, PostActionMixin, CreateView):
    form_class = CreatePostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class EditPost(LoginRequiredMixin, OnlyAuthorMixin,
               PostActionMixin, UpdateView):
    form_class = CreatePostForm

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', post.id)
        return super().dispatch(request, *args, **kwargs)


class DeletePost(LoginRequiredMixin, OnlyAuthorMixin,
                 PostActionMixin, DeleteView):

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            form=CreatePostForm(instance=self.object)
        )


class CommentAction:
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.object.post_id])


class CreateComment(LoginRequiredMixin, CommentAction, CreateView):
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)


class EditComment(LoginRequiredMixin, CommentAction, OnlyAuthorMixin,
                  UpdateView):
    form_class = CommentForm


class DeleteComment(LoginRequiredMixin, CommentAction, OnlyAuthorMixin,
                    DeleteView):
    pass


class Profile(DetailView):
    model = User
    context_object_name = 'profile'
    slug_url_kwarg = 'username'
    slug_field = 'username'
    template_name = 'blog/profile.html'
    paginate_by = PAGINATE_BY

    def get_context_data(self, **kwargs):
        posts = get_published_posts(
            published_check=False,
            for_user=self.object.id
        ).filter(author=self.object)
        return super().get_context_data(
            **kwargs,
            page_obj=create_paginator(
                posts,
                self.request.GET.get('page')
            )
        )


class EditProfile(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'
    success_url = reverse_lazy('blog:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])
