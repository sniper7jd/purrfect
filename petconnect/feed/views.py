"""Feed views."""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from petconnect.db import count_related
from pets.models import Follow, Pet

from .forms import PostForm, StoryForm
from .models import Comment, Post, PostLike, Story, StoryView

FEATURED_PETS_CACHE_KEY = "landing:featured_pets"
FEATURED_PETS_TTL = 300


def featured_pets():
    pets = cache.get(FEATURED_PETS_CACHE_KEY)
    if pets is None:
        pets = list(
            Pet.objects.filter(is_active=True)
            .annotate(followers_total=count_related(Follow, "pet"))
            .order_by("-followers_total", "-created_at")[:6]
        )
        cache.set(FEATURED_PETS_CACHE_KEY, pets, FEATURED_PETS_TTL)
    return pets


def with_post_stats(queryset, user):
    queryset = queryset.select_related("pet").annotate(
        like_total=count_related(PostLike, "post"),
        comment_total=count_related(Comment, "post"),
    )
    if user.is_authenticated:
        queryset = queryset.annotate(
            is_liked=Exists(PostLike.objects.filter(post=OuterRef("pk"), user=user))
        )
    return queryset


def home(request):
    if not request.user.is_authenticated:
        return render(request, "feed/landing.html", {"featured_pets": featured_pets()})

    pet_ids = set(Follow.objects.filter(follower=request.user).values_list("pet_id", flat=True))
    pet_ids.update(request.user.pets.values_list("id", flat=True))

    if pet_ids:
        posts = with_post_stats(Post.objects.filter(pet_id__in=pet_ids), request.user)
        posts = posts.order_by("-created_at")
    else:
        posts = with_post_stats(Post.objects.all(), request.user)
        posts = posts.order_by("-like_total", "-created_at")

    page = Paginator(posts, settings.POSTS_PER_PAGE).get_page(request.GET.get("page"))

    if request.htmx:
        return render(request, "feed/_post_list.html", {"page": page})

    stories = list(
        Story.objects.filter(pet_id__in=pet_ids, expires_at__gt=timezone.now())
        .select_related("pet")
        .order_by("-created_at")
    )
    seen_ids = set(
        StoryView.objects.filter(user=request.user, story__in=stories).values_list(
            "story_id", flat=True
        )
    )
    stories_by_pet = {}
    for story in stories:
        group = stories_by_pet.setdefault(
            story.pet_id, {"pet": story.pet, "stories": [], "has_unseen": False}
        )
        group["stories"].append(story)
        if story.id not in seen_ids:
            group["has_unseen"] = True

    return render(
        request,
        "feed/home.html",
        {
            "page": page,
            "stories_by_pet": stories_by_pet.values(),
            "has_pets": bool(request.user.pets.exists()),
        },
    )


@login_required
def create_post(request):
    user_pets = request.user.pets.all()
    if not user_pets:
        return redirect("pets:add")

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        pet = get_object_or_404(Pet, pk=request.POST.get("pet_id"), owner=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.pet = pet
            post.save()
            return redirect("feed:home")
    else:
        form = PostForm()

    return render(request, "feed/create_post.html", {"form": form, "user_pets": user_pets})


@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    deleted, _ = PostLike.objects.filter(user=request.user, post=post).delete()
    if not deleted:
        PostLike.objects.get_or_create(user=request.user, post=post)

    if request.htmx:
        post.is_liked = not deleted
        post.like_total = post.likes.count()
        return render(request, "feed/_like_button.html", {"post": post})
    return redirect("feed:post_detail", post_id=post.id)


@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    content = request.POST.get("content", "").strip()[:500]
    if not content:
        if request.htmx:
            return render(request, "feed/_comment.html", {"comment": None})
        return redirect("feed:post_detail", post_id=post.id)

    comment = Comment.objects.create(user=request.user, post=post, content=content)
    if request.htmx:
        return render(request, "feed/_comment.html", {"comment": comment})
    return redirect("feed:post_detail", post_id=post.id)


@login_required
def create_story(request):
    user_pets = request.user.pets.all()
    if not user_pets:
        return redirect("pets:add")

    if request.method == "POST":
        form = StoryForm(request.POST, request.FILES)
        pet = get_object_or_404(Pet, pk=request.POST.get("pet_id"), owner=request.user)
        if form.is_valid():
            story = form.save(commit=False)
            story.pet = pet
            story.save()
            return redirect("feed:home")
    else:
        form = StoryForm()

    return render(request, "feed/create_story.html", {"form": form, "user_pets": user_pets})


@login_required
def view_story(request, story_id):
    story = get_object_or_404(Story.objects.select_related("pet"), pk=story_id)
    if story.is_active:
        StoryView.objects.get_or_create(user=request.user, story=story)

    pet_stories = list(
        Story.objects.filter(pet=story.pet, expires_at__gt=timezone.now()).order_by("created_at")
    )
    index = next((i for i, s in enumerate(pet_stories) if s.id == story.id), 0)
    return render(
        request,
        "feed/view_story.html",
        {
            "story": story,
            "pet_stories": pet_stories,
            "next_story": pet_stories[index + 1] if index + 1 < len(pet_stories) else None,
        },
    )


def post_detail(request, post_id):
    post = get_object_or_404(with_post_stats(Post.objects.all(), request.user), pk=post_id)
    comments = post.comments.select_related("user")
    return render(request, "feed/post_detail.html", {"post": post, "comments": comments})


@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id, pet__owner=request.user)
    pet_id = post.pet_id
    post.delete()
    return redirect("pets:profile", pet_id=pet_id)
