"""Account views."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from feed.models import Post
from petconnect.db import count_related
from pets.models import Follow

from .forms import LoginForm, ProfileEditForm, RegisterForm

User = get_user_model()


def _safe_next(request, fallback="feed:home"):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return fallback


def login_view(request):
    if request.user.is_authenticated:
        return redirect("feed:home")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(_safe_next(request))
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


@require_POST
def demo_login(request):
    if not settings.DEMO_LOGIN_ENABLED:
        return redirect("accounts:login")
    demo_user = User.objects.filter(username=settings.DEMO_USERNAME, is_active=True).first()
    if demo_user is None:
        messages.error(request, "The demo account isn't set up yet. Run `manage.py seed_data`.")
        return redirect("accounts:login")
    login(request, demo_user, backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, "You're exploring PetConnect as the demo user. Have fun!")
    return redirect("feed:home")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("feed:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.name = form.cleaned_data.get("name")
            user.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("pets:add")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("feed:home")


@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    pets = list(
        profile_user.pets.annotate(
            posts_total=count_related(Post, "pet"),
            followers_total=count_related(Follow, "pet"),
        )
    )
    return render(
        request,
        "accounts/profile.html",
        {
            "profile_user": profile_user,
            "pets": pets,
            "follower_total": sum(pet.followers_total for pet in pets),
        },
    )


@login_required
def edit_profile_view(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("accounts:profile", username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, "accounts/edit_profile.html", {"form": form})
