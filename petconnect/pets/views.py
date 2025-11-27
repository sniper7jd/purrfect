"""Pet views."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Pet, Follow, Review
from .forms import PetForm, ReviewForm


@login_required
def add_pet(request):
    """Add a new pet."""
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            # Get location data from hidden fields
            pet.latitude = request.POST.get('latitude') or None
            pet.longitude = request.POST.get('longitude') or None
            pet.place_id = request.POST.get('place_id', '')
            pet.save()
            return redirect('pets:profile', pet_id=pet.id)
    else:
        form = PetForm()
    
    return render(request, 'pets/add_pet.html', {'form': form})


@login_required
def edit_pet(request, pet_id):
    """Edit a pet."""
    pet = get_object_or_404(Pet, pk=pet_id, owner=request.user)
    
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.latitude = request.POST.get('latitude') or pet.latitude
            pet.longitude = request.POST.get('longitude') or pet.longitude
            pet.place_id = request.POST.get('place_id') or pet.place_id
            pet.save()
            return redirect('pets:profile', pet_id=pet.id)
    else:
        form = PetForm(instance=pet)
    
    return render(request, 'pets/edit_pet.html', {'form': form, 'pet': pet})


@login_required
def delete_pet(request, pet_id):
    """Delete a pet."""
    pet = get_object_or_404(Pet, pk=pet_id, owner=request.user)
    
    if request.method == 'POST':
        pet.delete()
        return redirect('accounts:profile', username=request.user.username)
    
    return render(request, 'pets/delete_pet.html', {'pet': pet})


def pet_profile(request, pet_id):
    """View pet profile."""
    pet = get_object_or_404(Pet, pk=pet_id)
    reviews = pet.reviews.all()[:3]  # Latest 3 reviews
    
    # Check if current user follows this pet
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, pet=pet).exists()
    
    return render(request, 'pets/profile.html', {
        'pet': pet,
        'reviews': reviews,
        'is_following': is_following,
    })


@login_required
@require_POST
def follow_pet(request, pet_id):
    """Follow a pet."""
    pet = get_object_or_404(Pet, pk=pet_id)
    
    if pet.owner == request.user:
        return JsonResponse({'error': "You can't follow your own pet"}, status=400)
    
    follow, created = Follow.objects.get_or_create(follower=request.user, pet=pet)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'following',
            'follower_count': pet.follower_count
        })
    
    return redirect('pets:profile', pet_id=pet_id)


@login_required
@require_POST
def unfollow_pet(request, pet_id):
    """Unfollow a pet."""
    pet = get_object_or_404(Pet, pk=pet_id)
    Follow.objects.filter(follower=request.user, pet=pet).delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'not_following',
            'follower_count': pet.follower_count
        })
    
    return redirect('pets:profile', pet_id=pet_id)


@login_required
def add_review(request, pet_id):
    """Add a review for a pet."""
    pet = get_object_or_404(Pet, pk=pet_id)
    
    if pet.owner == request.user:
        return redirect('pets:profile', pet_id=pet_id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.pet = pet
            review.reviewer = request.user
            review.save()
            return redirect('pets:profile', pet_id=pet_id)
    else:
        form = ReviewForm()
    
    return render(request, 'pets/add_review.html', {'form': form, 'pet': pet})


def all_reviews(request, pet_id):
    """View all reviews for a pet."""
    pet = get_object_or_404(Pet, pk=pet_id)
    reviews = pet.reviews.all()
    
    return render(request, 'pets/all_reviews.html', {'pet': pet, 'reviews': reviews})



