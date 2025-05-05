from django.contrib import admin

from .models import Category, Location, Post, Comment


class CommentInline(admin.StackedInline):
    model = Comment
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = (
        CommentInline,
    )
    list_display = (
        'title',
        'text',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published',
        'created_at',
    )
    search_fields = ('title',)
    list_editable = ('is_published',)
    empty_value_display = 'Не задано'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'description',
        'slug',
        'is_published',
        'created_at'
    )
    search_fields = ('title',)
    list_editable = ('is_published',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_published',
        'created_at'
    )
    search_fields = ('name',)
    list_editable = ('is_published',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'text',
        'author',
        'post',
        'pub_date',
    )
