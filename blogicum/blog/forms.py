from django import forms
from django.contrib.auth import get_user_model

from .models import Post, Comment


class CreatePostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'category', 'location', 'pub_date', 'image']
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'date'})
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'username', 'email']
