"""Seed database with sample data."""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from pets.models import Pet, Follow
from feed.models import Post
from datetime import timedelta
from django.utils import timezone
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with sample users, pets, and posts'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # Create sample users
        users_data = [
            {'username': 'alexchen', 'name': 'Alex Chen', 'email': 'alex@example.com', 'location': 'South Hill, NY', 'email_verified': True},
            {'username': 'sarahk', 'name': 'Sarah Kim', 'email': 'sarah@example.com', 'location': 'Downtown, NY', 'email_verified': True, 'id_verified': True},
            {'username': 'mikebrown', 'name': 'Mike Brown', 'email': 'mike@example.com', 'location': 'Northside, NY'},
            {'username': 'emilyw', 'name': 'Emily White', 'email': 'emily@example.com', 'location': 'Collegetown, NY', 'email_verified': True},
        ]
        
        users = []
        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'name': data['name'],
                    'email': data['email'],
                    'location': data.get('location', ''),
                    'email_verified': data.get('email_verified', False),
                    'id_verified': data.get('id_verified', False),
                    'response_rate': random.randint(80, 100),
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'  Created user: {user.username}')
            users.append(user)
        
        # Create sample pets
        pets_data = [
            {
                'owner': users[0],
                'name': 'Buddy',
                'species': 'Dog',
                'breed': 'Golden Retriever',
                'bio': "Hi, I'm Buddy! My friends would describe me as a professional stick-chaser, a certified good boy, and an expert-level cuddle enthusiast. My favorite things are long walks, the crinkle of a treat bag, and making new friends!",
                'age_years': 4,
                'weight_lbs': 75,
                'gender': 'male_neutered',
                'energy_level': 'high',
                'temperament': 'friendly',
                'training_level': 'advanced',
                'good_with_dogs': True,
                'good_with_cats': True,
                'good_with_kids': True,
                'vaccinations_current': True,
                'microchipped': True,
                'temperament_assessed': True,
                'location': 'South Hill, NY',
                'latitude': 42.4354,
                'longitude': -76.4815,
            },
            {
                'owner': users[1],
                'name': 'Luna',
                'species': 'Cat',
                'breed': 'Domestic Shorthair',
                'bio': "I'm Luna, a sophisticated feline who appreciates the finer things in life—like cardboard boxes and sunny windowsills. I'm selective with my friendships but loyal to those I choose.",
                'age_years': 2,
                'age_months': 6,
                'weight_lbs': 9,
                'gender': 'female_spayed',
                'energy_level': 'medium',
                'temperament': 'calm',
                'good_with_cats': True,
                'vaccinations_current': True,
                'location': 'Downtown, NY',
                'latitude': 42.4396,
                'longitude': -76.4967,
            },
            {
                'owner': users[2],
                'name': 'Max',
                'species': 'Dog',
                'breed': 'Pug',
                'bio': "Snort, wheeze, and lots of love! That's me, Max. I may be small but I've got a huge personality. I love naps, treats, and more naps.",
                'age_years': 5,
                'weight_lbs': 22,
                'gender': 'male',
                'energy_level': 'low',
                'temperament': 'friendly',
                'good_with_dogs': True,
                'good_with_kids': True,
                'vaccinations_current': True,
                'microchipped': True,
                'location': 'Northside, NY',
                'latitude': 42.4534,
                'longitude': -76.4735,
            },
            {
                'owner': users[0],
                'name': 'Daisy',
                'species': 'Dog',
                'breed': 'Beagle',
                'bio': "Follow my nose wherever it goes! I'm Daisy, an adventurous beagle who loves exploring. If there's a scent to track, I'm on the case!",
                'age_years': 3,
                'weight_lbs': 28,
                'gender': 'female_spayed',
                'energy_level': 'high',
                'temperament': 'playful',
                'training_level': 'basic',
                'good_with_dogs': True,
                'good_with_kids': True,
                'vaccinations_current': True,
                'location': 'South Hill, NY',
                'latitude': 42.4334,
                'longitude': -76.4855,
            },
            {
                'owner': users[3],
                'name': 'Leo',
                'species': 'Cat',
                'breed': 'Bengal Mix',
                'bio': "They call me Leo the explorer. I'm an adventurous Bengal mix who loves climbing, playing, and occasionally getting into mischief. Never a dull moment!",
                'age_years': 3,
                'weight_lbs': 12,
                'gender': 'male_neutered',
                'energy_level': 'high',
                'temperament': 'playful',
                'good_with_cats': True,
                'vaccinations_current': True,
                'location': 'Collegetown, NY',
                'latitude': 42.4426,
                'longitude': -76.4847,
            },
        ]
        
        pets = []
        for data in pets_data:
            pet, created = Pet.objects.get_or_create(
                owner=data.pop('owner'),
                name=data['name'],
                defaults=data
            )
            if created:
                self.stdout.write(f'  Created pet: {pet.name}')
            pets.append(pet)
        
        # Create some follows
        for user in users:
            for pet in random.sample(pets, k=min(3, len(pets))):
                if pet.owner != user:
                    Follow.objects.get_or_create(follower=user, pet=pet)
        
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write('Sample login: alexchen / password123')

