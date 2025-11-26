"""Playdates and discovery views."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.conf import settings

from pets.models import Pet


def discover(request):
    """Discover pets for playdates with smart matching."""
    # Base query - active pets available for playdate
    pets_query = Pet.objects.filter(is_active=True, available_for_playdate=True)
    
    # Search filter
    search = request.GET.get('search', '').strip()
    if search:
        pets_query = pets_query.filter(
            Q(name__icontains=search) |
            Q(breed__icontains=search) |
            Q(species__icontains=search)
        )
    
    # Species filter
    species = request.GET.get('species', '')
    if species:
        pets_query = pets_query.filter(species=species)
    
    # Age filter
    age = request.GET.get('age', '')
    if age == '0-2':
        pets_query = pets_query.filter(Q(age_years__lt=2) | Q(age_years=2, age_months=0))
    elif age == '3-5':
        pets_query = pets_query.filter(age_years__gte=3, age_years__lte=5)
    elif age == '6+':
        pets_query = pets_query.filter(age_years__gte=6)
    
    # Smart matching filters
    temperament = request.GET.get('temperament', '')
    if temperament:
        pets_query = pets_query.filter(temperament=temperament)
    
    energy = request.GET.get('energy', '')
    if energy:
        pets_query = pets_query.filter(energy_level=energy)
    
    training = request.GET.get('training', '')
    if training:
        pets_query = pets_query.filter(training_level=training)
    
    social = request.GET.get('social', '')
    if social:
        pets_query = pets_query.filter(social_preference=social)
    
    # Sort
    sort = request.GET.get('sort', '')
    if sort == 'alpha_asc':
        pets_query = pets_query.order_by('name')
    elif sort == 'alpha_desc':
        pets_query = pets_query.order_by('-name')
    elif sort == 'location':
        pets_query = pets_query.order_by('location')
    elif sort == 'popular':
        pets_query = pets_query.annotate(followers_count=Count('followers')).order_by('-followers_count')
    else:
        pets_query = pets_query.order_by('-created_at')
    
    # Exclude user's own pets if authenticated
    if request.user.is_authenticated:
        pets_query = pets_query.exclude(owner=request.user)
    
    # Pagination
    paginator = Paginator(pets_query, settings.PETS_PER_PAGE)
    page = request.GET.get('page', 1)
    pets = paginator.get_page(page)
    
    # Get species choices for filter
    species_choices = Pet.objects.filter(
        is_active=True
    ).values_list('species', flat=True).distinct().order_by('species')
    
    return render(request, 'playdates/discover.html', {
        'pets': pets,
        'species_choices': species_choices,
    })


def suggest(request):
    """Autocomplete suggestions for pet search."""
    query = request.GET.get('query', '').lower()
    suggestions = []
    
    if len(query) >= 2:
        # Search pets
        pets = Pet.objects.filter(
            Q(name__icontains=query) |
            Q(breed__icontains=query) |
            Q(species__icontains=query),
            is_active=True
        )[:10]
        
        seen = set()
        for pet in pets:
            if pet.name.lower() not in seen:
                suggestions.append({'text': pet.name, 'type': 'name'})
                seen.add(pet.name.lower())
            if pet.breed and pet.breed.lower() not in seen:
                suggestions.append({'text': pet.breed, 'type': 'breed'})
                seen.add(pet.breed.lower())
            if pet.species.lower() not in seen:
                suggestions.append({'text': pet.species, 'type': 'species'})
                seen.add(pet.species.lower())
    
    return JsonResponse(suggestions[:8], safe=False)


@login_required
def smart_match(request):
    """Find compatible playmates based on user's pet profile."""
    # Get user's pets
    user_pets = request.user.pets.filter(is_active=True)
    
    if not user_pets.exists():
        return render(request, 'playdates/smart_match.html', {
            'no_pets': True
        })
    
    # Get selected pet or default to first pet
    pet_id = request.GET.get('pet_id')
    if pet_id:
        selected_pet = get_object_or_404(Pet, pk=pet_id, owner=request.user)
    else:
        selected_pet = user_pets.first()
    
    # Find compatible pets
    compatible_pets = Pet.objects.filter(
        is_active=True,
        available_for_playdate=True
    ).exclude(owner=request.user)
    
    # Match by species (dogs play with dogs, etc.)
    if selected_pet.species:
        compatible_pets = compatible_pets.filter(species=selected_pet.species)
    
    # Match by energy level (similar or one level apart)
    energy_matches = {
        'low': ['low', 'medium'],
        'medium': ['low', 'medium', 'high'],
        'high': ['medium', 'high'],
    }
    if selected_pet.energy_level in energy_matches:
        compatible_pets = compatible_pets.filter(
            energy_level__in=energy_matches[selected_pet.energy_level]
        )
    
    # Check compatibility (if pet is good with dogs, find dogs that are good with dogs)
    if selected_pet.species == 'Dog':
        compatible_pets = compatible_pets.filter(good_with_dogs=True)
    elif selected_pet.species == 'Cat':
        compatible_pets = compatible_pets.filter(good_with_cats=True)
    
    # Order by match quality
    compatible_pets = compatible_pets.annotate(
        followers_count=Count('followers')
    ).order_by('-followers_count')[:12]
    
    return render(request, 'playdates/smart_match.html', {
        'selected_pet': selected_pet,
        'user_pets': user_pets,
        'compatible_pets': compatible_pets,
    })


def map_view(request):
    """View pets on a map. Optionally center on a specific pet."""
    # Check if a specific pet is requested
    focus_pet_id = request.GET.get('pet')
    focus_pet = None
    
    if focus_pet_id:
        try:
            focus_pet = Pet.objects.get(
                pk=focus_pet_id,
                is_active=True,
                latitude__isnull=False,
                longitude__isnull=False
            )
        except Pet.DoesNotExist:
            pass
    
    pets = Pet.objects.filter(
        is_active=True,
        available_for_playdate=True,
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    # Determine center point
    if focus_pet:
        avg_lat = focus_pet.latitude
        avg_lng = focus_pet.longitude
        zoom_level = 14  # Closer zoom when focusing on specific pet
    elif pets.exists():
        avg_lat = sum(p.latitude for p in pets) / len(pets)
        avg_lng = sum(p.longitude for p in pets) / len(pets)
        zoom_level = 12
    else:
        avg_lat, avg_lng = 42.4534, -76.4735  # Default to Ithaca, NY
        zoom_level = 10
    
    pet_data = [{
        'id': pet.id,
        'name': pet.name,
        'species': pet.species,
        'breed': pet.breed,
        'latitude': pet.latitude,
        'longitude': pet.longitude,
        'image_url': pet.picture.url if pet.picture else None,
        'profile_url': pet.get_absolute_url(),
        'is_focus': focus_pet and pet.id == focus_pet.id,
    } for pet in pets]
    
    return render(request, 'playdates/map.html', {
        'pets': pet_data,
        'avg_lat': avg_lat,
        'avg_lng': avg_lng,
        'zoom_level': zoom_level,
        'focus_pet': focus_pet,
    })



