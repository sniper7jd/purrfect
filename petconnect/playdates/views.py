"""Playdate discovery, smart matching, and the map."""

import math

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import (
    Avg,
    Case,
    ExpressionWrapper,
    F,
    FloatField,
    IntegerField,
    Q,
    Value,
    When,
)
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from petconnect.db import count_related
from pets.models import Follow, Pet

DEFAULT_CENTER = (42.4440, -76.5019)  # Ithaca, NY, where the seed data lives
KM_PER_DEGREE = 111.32

ENERGY_LEVELS = {"low": 0, "medium": 1, "high": 2}

MATCH_WEIGHTS = {
    "energy_exact": 3,
    "energy_adjacent": 1,
    "temperament": 2,
    "social": 1,
    "training": 1,
    "vaccinated": 1,
    "nearby": 3,
    "same_area": 1,
}
MAX_MATCH_SCORE = (
    MATCH_WEIGHTS["energy_exact"]
    + MATCH_WEIGHTS["temperament"]
    + MATCH_WEIGHTS["social"]
    + MATCH_WEIGHTS["training"]
    + MATCH_WEIGHTS["vaccinated"]
    + MATCH_WEIGHTS["nearby"]
)


def _available_pets():
    return Pet.objects.filter(is_active=True, available_for_playdate=True)


def discover(request):
    pets_query = _available_pets()

    search = request.GET.get("search", "").strip()
    if search:
        pets_query = pets_query.filter(
            Q(name__icontains=search) | Q(breed__icontains=search) | Q(species__icontains=search)
        )

    filters = {
        "species": "species",
        "temperament": "temperament",
        "energy": "energy_level",
        "training": "training_level",
        "social": "social_preference",
    }
    for param, field in filters.items():
        value = request.GET.get(param, "")
        if value:
            pets_query = pets_query.filter(**{field: value})

    age = request.GET.get("age", "")
    if age == "0-2":
        pets_query = pets_query.filter(Q(age_years__lt=2) | Q(age_years=2, age_months=0))
    elif age == "3-5":
        pets_query = pets_query.filter(age_years__gte=3, age_years__lte=5)
    elif age == "6+":
        pets_query = pets_query.filter(age_years__gte=6)

    sort = request.GET.get("sort", "")
    if sort == "alpha_asc":
        pets_query = pets_query.order_by("name")
    elif sort == "alpha_desc":
        pets_query = pets_query.order_by("-name")
    elif sort == "popular":
        pets_query = pets_query.annotate(followers_total=count_related(Follow, "pet")).order_by(
            "-followers_total", "-created_at"
        )
    else:
        pets_query = pets_query.order_by("-created_at")

    if request.user.is_authenticated:
        pets_query = pets_query.exclude(owner=request.user)

    pets = Paginator(pets_query, settings.PETS_PER_PAGE).get_page(request.GET.get("page"))
    species_choices = (
        Pet.objects.filter(is_active=True)
        .values_list("species", flat=True)
        .distinct()
        .order_by("species")
    )
    return render(
        request, "playdates/discover.html", {"pets": pets, "species_choices": species_choices}
    )


def suggest(request):
    """Autocomplete suggestions for the discover search box."""
    query = request.GET.get("query", "").strip()
    suggestions = []
    if len(query) >= 2:
        pets = Pet.objects.filter(
            Q(name__icontains=query) | Q(breed__icontains=query) | Q(species__icontains=query),
            is_active=True,
        ).values_list("name", "breed", "species")[:10]
        seen = set()
        for name, breed, species in pets:
            for text, kind in ((name, "name"), (breed, "breed"), (species, "species")):
                if text and text.lower() not in seen and query.lower() in text.lower():
                    suggestions.append({"text": text, "type": kind})
                    seen.add(text.lower())
    return JsonResponse(suggestions[:8], safe=False)


def distance_km(lat1, lng1, lat2, lng2):
    """Great-circle distance (haversine)."""
    lat1, lng1, lat2, lng2 = map(math.radians, (lat1, lng1, lat2, lng2))
    a = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    )
    return 2 * 6371 * math.asin(math.sqrt(a))


def ranked_matches(pet, limit=12):
    """Compatible playmates for `pet`, ranked by a weighted compatibility score.

    Hard requirements (same species, available, safe with this species) are filters;
    everything else adds points, so close-but-imperfect matches still show up, lower down.
    """
    candidates = _available_pets().exclude(owner_id=pet.owner_id).filter(species=pet.species)
    if pet.species == "Dog":
        candidates = candidates.filter(good_with_dogs=True)
    elif pet.species == "Cat":
        candidates = candidates.filter(good_with_cats=True)

    level = ENERGY_LEVELS.get(pet.energy_level, 1)
    adjacent = [name for name, value in ENERGY_LEVELS.items() if abs(value - level) == 1]
    score = (
        Case(
            When(energy_level=pet.energy_level, then=Value(MATCH_WEIGHTS["energy_exact"])),
            When(energy_level__in=adjacent, then=Value(MATCH_WEIGHTS["energy_adjacent"])),
            default=Value(0),
        )
        + Case(
            When(temperament=pet.temperament, then=Value(MATCH_WEIGHTS["temperament"])),
            default=Value(0),
        )
        + Case(
            When(social_preference=pet.social_preference, then=Value(MATCH_WEIGHTS["social"])),
            default=Value(0),
        )
        + Case(
            When(training_level=pet.training_level, then=Value(MATCH_WEIGHTS["training"])),
            default=Value(0),
        )
        + Case(
            When(vaccinations_current=True, then=Value(MATCH_WEIGHTS["vaccinated"])),
            default=Value(0),
        )
    )

    if pet.latitude is not None and pet.longitude is not None:
        # Equirectangular approximation: accurate enough for "within a few km" scoring,
        # and it runs in the database on both PostgreSQL and SQLite.
        lng_scale = math.cos(math.radians(pet.latitude))
        dlat = F("latitude") - pet.latitude
        dlng = (F("longitude") - pet.longitude) * lng_scale
        candidates = candidates.annotate(
            squared_degrees=ExpressionWrapper(dlat * dlat + dlng * dlng, output_field=FloatField())
        )
        score = score + Case(
            When(
                squared_degrees__lte=(5 / KM_PER_DEGREE) ** 2, then=Value(MATCH_WEIGHTS["nearby"])
            ),
            When(
                squared_degrees__lte=(20 / KM_PER_DEGREE) ** 2,
                then=Value(MATCH_WEIGHTS["same_area"]),
            ),
            default=Value(0),
        )

    matches = list(
        candidates.annotate(
            match_score=ExpressionWrapper(score, output_field=IntegerField())
        ).order_by("-match_score", "-created_at")[:limit]
    )
    for match in matches:
        match.match_percent = round(100 * match.match_score / MAX_MATCH_SCORE)
        match.distance_km = (
            distance_km(pet.latitude, pet.longitude, match.latitude, match.longitude)
            if None not in (pet.latitude, pet.longitude, match.latitude, match.longitude)
            else None
        )
    return matches


@login_required
def smart_match(request):
    user_pets = request.user.pets.filter(is_active=True)
    if not user_pets.exists():
        return render(request, "playdates/smart_match.html", {"no_pets": True})

    pet_id = request.GET.get("pet_id")
    selected_pet = (
        get_object_or_404(user_pets, pk=pet_id)
        if pet_id
        else user_pets.order_by("created_at").first()
    )
    return render(
        request,
        "playdates/smart_match.html",
        {
            "selected_pet": selected_pet,
            "user_pets": user_pets,
            "compatible_pets": ranked_matches(selected_pet),
        },
    )


def _pet_marker(pet):
    return {
        "id": pet.id,
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "latitude": pet.latitude,
        "longitude": pet.longitude,
        "image_url": pet.picture.url if pet.picture else None,
        "profile_url": pet.get_absolute_url(),
    }


def map_view(request):
    located = _available_pets().filter(latitude__isnull=False, longitude__isnull=False)
    focus_pet = None
    focus_id = request.GET.get("pet")
    if focus_id and focus_id.isdigit():
        focus_pet = (
            Pet.objects.filter(
                pk=focus_id, is_active=True, latitude__isnull=False, longitude__isnull=False
            )
            .only("id", "name", "species", "breed", "latitude", "longitude", "picture", "location")
            .first()
        )

    if focus_pet:
        center, zoom = (focus_pet.latitude, focus_pet.longitude), 14
    else:
        averages = located.aggregate(lat=Avg("latitude"), lng=Avg("longitude"))
        if averages["lat"] is not None:
            center, zoom = (averages["lat"], averages["lng"]), 12
        else:
            center, zoom = DEFAULT_CENTER, 10

    config = {
        "center": {"lat": center[0], "lng": center[1]},
        "zoom": zoom,
        "endpoint": reverse("playdates:map_pets"),
        "focusPetId": focus_pet.id if focus_pet else None,
        "focusPet": _pet_marker(focus_pet) if focus_pet else None,
    }
    return render(request, "playdates/map.html", {"map_config": config, "focus_pet": focus_pet})


def _float_param(request, name, low, high):
    try:
        value = float(request.GET[name])
    except (KeyError, ValueError):
        return None
    return min(max(value, low), high)


@require_GET
def map_pets(request):
    """Pets inside the map's visible bounds (JSON), capped at MAP_MAX_PETS."""
    south = _float_param(request, "south", -90, 90)
    north = _float_param(request, "north", -90, 90)
    west = _float_param(request, "west", -180, 180)
    east = _float_param(request, "east", -180, 180)
    if None in (south, north, west, east):
        return JsonResponse({"error": "south, north, west and east are required"}, status=400)

    pets = _available_pets().filter(latitude__range=(south, north))
    if west <= east:
        pets = pets.filter(longitude__range=(west, east))
    else:
        pets = pets.filter(Q(longitude__gte=west) | Q(longitude__lte=east))

    limit = settings.MAP_MAX_PETS
    rows = list(
        pets.only("id", "name", "species", "breed", "latitude", "longitude", "picture").order_by(
            "-created_at"
        )[: limit + 1]
    )
    return JsonResponse(
        {"pets": [_pet_marker(pet) for pet in rows[:limit]], "truncated": len(rows) > limit}
    )
