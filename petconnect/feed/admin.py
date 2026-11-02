"""Feed admin."""

from django.contrib import admin

from petconnect.db import count_related

from .models import Comment, Post, PostLike, Story, StoryView


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["pet", "created_at", "like_total", "comment_total"]
    list_filter = ["created_at"]
    list_select_related = ["pet"]
    raw_id_fields = ["pet"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                like_total=count_related(PostLike, "post"),
                comment_total=count_related(Comment, "post"),
            )
        )

    @admin.display(ordering="like_total", description="Likes")
    def like_total(self, obj):
        return obj.like_total

    @admin.display(ordering="comment_total", description="Comments")
    def comment_total(self, obj):
        return obj.comment_total


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ["user", "post", "created_at"]
    raw_id_fields = ["user", "post"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["user", "post", "created_at"]
    raw_id_fields = ["user", "post"]


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ["pet", "created_at", "expires_at", "is_active"]
    list_filter = ["created_at"]
    raw_id_fields = ["pet"]


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ["user", "story", "viewed_at"]
    raw_id_fields = ["user", "story"]
