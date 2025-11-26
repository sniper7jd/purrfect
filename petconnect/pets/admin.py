"""Pet admin."""
from django.contrib import admin
from .models import Pet, Follow, Review


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'species', 'breed', 'is_active', 'created_at']
    list_filter = ['species', 'is_active', 'vaccinations_current', 'energy_level']
    search_fields = ['name', 'breed', 'owner__username']
    raw_id_fields = ['owner']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'pet', 'created_at']
    raw_id_fields = ['follower', 'pet']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['pet', 'reviewer', 'rating', 'review_type', 'created_at']
    list_filter = ['rating', 'review_type']
    raw_id_fields = ['pet', 'reviewer']

