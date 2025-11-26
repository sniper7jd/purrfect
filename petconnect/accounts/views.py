"""Account views."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model

from .forms import LoginForm, RegisterForm, ProfileEditForm

User = get_user_model()


def login_view(request):
    """User login."""
    if request.user.is_authenticated:
        return redirect('feed:home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'feed:home')
            return redirect(next_url)
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    """User registration."""
    if request.user.is_authenticated:
        return redirect('feed:home')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.name = form.cleaned_data.get('name')
            user.save()
            login(request, user)
            messages.success(request, 'Welcome to PetConnect! Add your first pet to get started.')
            return redirect('pets:add')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    """User logout."""
    logout(request)
    return redirect('feed:home')


@login_required
def profile_view(request, username):
    """View user profile with their pets."""
    profile_user = get_object_or_404(User, username=username)
    pets = profile_user.pets.all()
    
    return render(request, 'accounts/profile.html', {
        'profile_user': profile_user,
        'pets': pets,
    })


@login_required
def edit_profile_view(request):
    """Edit user profile."""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})

