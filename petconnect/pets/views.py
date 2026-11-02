"""Pet views."""

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from feed.models import Post
from petconnect.db import count_related

from .forms import PetForm, ReviewForm
from .models import Follow, Pet


@login_required
def add_pet(request):
    if request.method == "POST":
        form = PetForm(request.POST, request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            pet.save()
            return redirect("pets:profile", pet_id=pet.id)
    else:
        form = PetForm()

    return render(request, "pets/pet_form.html", {"form": form})


@login_required
def edit_pet(request, pet_id):
    pet = get_object_or_404(Pet, pk=pet_id, owner=request.user)

    if request.method == "POST":
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            form.save()
            return redirect("pets:profile", pet_id=pet.id)
    else:
        form = PetForm(instance=pet)

    return render(request, "pets/pet_form.html", {"form": form, "pet": pet})


@login_required
def delete_pet(request, pet_id):
    pet = get_object_or_404(Pet, pk=pet_id, owner=request.user)

    if request.method == "POST":
        pet.delete()
        return redirect("accounts:profile", username=request.user.username)

    return render(request, "pets/delete_pet.html", {"pet": pet})


def _pet_with_counts():
    return Pet.objects.select_related("owner").annotate(
        posts_total=count_related(Post, "pet"),
        followers_total=count_related(Follow, "pet"),
    )


def pet_profile(request, pet_id):
    pet = get_object_or_404(_pet_with_counts(), pk=pet_id)
    review_stats = pet.reviews.aggregate(total=Count("id"), average=Avg("rating"))
    is_following = (
        request.user.is_authenticated
        and Follow.objects.filter(follower=request.user, pet=pet).exists()
    )
    return render(
        request,
        "pets/profile.html",
        {
            "pet": pet,
            "posts": pet.posts.only("id", "image", "pet_id")[:30],
            "reviews": pet.reviews.select_related("reviewer")[:3],
            "review_stats": review_stats,
            "is_following": is_following,
        },
    )


def _follow_response(request, pet_id, is_following):
    if request.htmx:
        pet = get_object_or_404(_pet_with_counts(), pk=pet_id)
        return render(
            request,
            "pets/_follow_button.html",
            {"pet": pet, "is_following": is_following, "oob": True},
        )
    return redirect("pets:profile", pet_id=pet_id)


@login_required
@require_POST
def follow_pet(request, pet_id):
    pet = get_object_or_404(Pet, pk=pet_id)
    if pet.owner_id == request.user.id:
        return HttpResponseBadRequest("You can't follow your own pet.")
    Follow.objects.get_or_create(follower=request.user, pet=pet)
    return _follow_response(request, pet_id, True)


@login_required
@require_POST
def unfollow_pet(request, pet_id):
    Follow.objects.filter(follower=request.user, pet_id=pet_id).delete()
    return _follow_response(request, pet_id, False)


@login_required
def add_review(request, pet_id):
    pet = get_object_or_404(Pet, pk=pet_id)
    if pet.owner_id == request.user.id:
        return redirect("pets:profile", pet_id=pet_id)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.pet = pet
            review.reviewer = request.user
            review.save()
            return redirect("pets:profile", pet_id=pet_id)
    else:
        form = ReviewForm()

    return render(request, "pets/add_review.html", {"form": form, "pet": pet})


def all_reviews(request, pet_id):
    pet = get_object_or_404(Pet, pk=pet_id)
    reviews = pet.reviews.select_related("reviewer")
    review_stats = reviews.aggregate(total=Count("id"), average=Avg("rating"))
    return render(
        request,
        "pets/all_reviews.html",
        {"pet": pet, "reviews": reviews, "review_stats": review_stats},
    )
