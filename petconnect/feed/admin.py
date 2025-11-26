"""Feed admin."""
from django.contrib import admin
from .models import Post, PostLike, Comment, Story, StoryView


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['pet', 'created_at', 'like_count', 'comment_count']
    list_filter = ['created_at']
    raw_id_fields = ['pet']


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    raw_id_fields = ['user', 'post']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    raw_id_fields = ['user', 'post']


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['pet', 'created_at', 'expires_at', 'is_active']
    list_filter = ['created_at']
    raw_id_fields = ['pet']


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ['user', 'story', 'viewed_at']
    raw_id_fields = ['user', 'story']



