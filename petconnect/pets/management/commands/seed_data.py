"""Seed the database with demo users, pets, posts, reviews, and conversations.

Idempotent: safe to run on every deploy. Existing rows are left alone.
"""

from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from chat.models import Conversation, Message
from feed.models import Comment, Post, PostLike
from pets.models import Follow, Pet, Review

User = get_user_model()
IMAGES_DIR = Path(__file__).resolve().parent.parent / "seed_images"
SAMPLE_PASSWORD = "petconnect-demo"

USERS = [
    {
        "username": "alexchen",
        "name": "Alex Chen",
        "location": "South Hill, Ithaca",
        "email_verified": True,
    },
    {
        "username": "sarahk",
        "name": "Sarah Kim",
        "location": "Downtown Ithaca",
        "email_verified": True,
        "id_verified": True,
    },
    {"username": "mikebrown", "name": "Mike Brown", "location": "Northside, Ithaca"},
    {
        "username": "emilyw",
        "name": "Emily White",
        "location": "Collegetown, Ithaca",
        "email_verified": True,
    },
]

PETS = [
    {
        "owner": "alexchen",
        "name": "Buddy",
        "species": "Dog",
        "breed": "Golden Retriever",
        "image": "golden-retriever.jpg",
        "age_years": 4,
        "weight_lbs": 75,
        "gender": "male_neutered",
        "energy_level": "high",
        "temperament": "friendly",
        "training_level": "advanced",
        "good_with_cats": True,
        "microchipped": True,
        "temperament_assessed": True,
        "location": "South Hill, Ithaca",
        "latitude": 42.4254,
        "longitude": -76.4945,
        "bio": "Professional stick-chaser, certified good boy, and expert-level cuddler. Will trade high-fives for treats.",
        "caption": "Golden hour, golden boy. Who wants to play fetch? #goldenretriever #parkday",
    },
    {
        "owner": "alexchen",
        "name": "Daisy",
        "species": "Dog",
        "breed": "Beagle",
        "image": "beagle.jpg",
        "age_years": 3,
        "weight_lbs": 28,
        "gender": "female_spayed",
        "energy_level": "high",
        "temperament": "playful",
        "training_level": "basic",
        "location": "South Hill, Ithaca",
        "latitude": 42.4301,
        "longitude": -76.4880,
        "bio": "Follow my nose wherever it goes! If there's a scent to track, I'm on the case.",
        "caption": "Nose: activated. Squirrel: not found (yet). #beagle",
    },
    {
        "owner": "sarahk",
        "name": "Luna",
        "species": "Cat",
        "breed": "Domestic Shorthair",
        "image": "tuxedo-cat.jpg",
        "age_years": 2,
        "age_months": 6,
        "weight_lbs": 9,
        "gender": "female_spayed",
        "energy_level": "medium",
        "temperament": "calm",
        "social_preference": "selective",
        "good_with_dogs": False,
        "good_with_cats": True,
        "location": "Downtown Ithaca",
        "latitude": 42.4396,
        "longitude": -76.4967,
        "bio": "A sophisticated feline who appreciates cardboard boxes and sunny windowsills. Selective with friendships, loyal forever.",
        "caption": "Supervising the neighborhood from my office. #tuxedocat",
    },
    {
        "owner": "sarahk",
        "name": "Pepper",
        "species": "Dog",
        "breed": "Pembroke Welsh Corgi",
        "image": "corgi-puppy.jpg",
        "age_years": 0,
        "age_months": 7,
        "weight_lbs": 14,
        "gender": "female",
        "energy_level": "high",
        "temperament": "playful",
        "training_level": "in_training",
        "location": "Fall Creek, Ithaca",
        "latitude": 42.4486,
        "longitude": -76.4920,
        "bio": "Tiny legs, enormous zoomies. Currently mastering 'sit' and 'please stop chewing that'.",
        "caption": "First week of puppy class and I'm already the teacher's pet. #corgipuppy",
    },
    {
        "owner": "mikebrown",
        "name": "Max",
        "species": "Dog",
        "breed": "Pug",
        "image": "pug.jpg",
        "age_years": 5,
        "weight_lbs": 22,
        "gender": "male",
        "energy_level": "low",
        "temperament": "friendly",
        "social_preference": "one_on_one",
        "microchipped": True,
        "location": "Northside, Ithaca",
        "latitude": 42.4534,
        "longitude": -76.4935,
        "bio": "Snort, wheeze, and lots of love. Small dog, huge personality. Hobbies: naps, treats, more naps.",
        "caption": "Sweater weather is my favorite weather. #pug",
    },
    {
        "owner": "mikebrown",
        "name": "Bear",
        "species": "Dog",
        "breed": "Chow Chow",
        "image": "chow-chow.jpg",
        "age_years": 6,
        "weight_lbs": 55,
        "gender": "male_neutered",
        "energy_level": "medium",
        "temperament": "independent",
        "social_preference": "slow_intro",
        "location": "Cayuga Heights",
        "latitude": 42.4632,
        "longitude": -76.4865,
        "bio": "Fluffy, dignified, and extremely cool. Warms up slowly, then never leaves your side.",
        "caption": "Too cool for the dog park. (Not really, please invite me.) #chowchow",
    },
    {
        "owner": "emilyw",
        "name": "Leo",
        "species": "Cat",
        "breed": "Orange Tabby",
        "image": "orange-cat-lounging.jpg",
        "age_years": 3,
        "weight_lbs": 12,
        "gender": "male_neutered",
        "energy_level": "high",
        "temperament": "playful",
        "good_with_dogs": True,
        "good_with_cats": True,
        "location": "Collegetown, Ithaca",
        "latitude": 42.4426,
        "longitude": -76.4847,
        "bio": "Leo the explorer: climbing, pouncing, and occasionally knocking things off tables on purpose.",
        "caption": "Caught mid-plan. You'll never know what I was plotting. #orangecat",
    },
    {
        "owner": "emilyw",
        "name": "Scout",
        "species": "Dog",
        "breed": "Australian Shepherd",
        "image": "australian-shepherd.jpg",
        "age_years": 2,
        "weight_lbs": 48,
        "gender": "female_spayed",
        "energy_level": "high",
        "temperament": "friendly",
        "training_level": "advanced",
        "good_with_cats": True,
        "temperament_assessed": True,
        "location": "Stewart Park, Ithaca",
        "latitude": 42.4610,
        "longitude": -76.5050,
        "bio": "Herder of balls, frisbees, and occasionally people. Looking for friends who can keep up.",
        "caption": "Beach day at the lake! Who wants to race? #aussie",
    },
    {
        "owner": "demo",
        "name": "Mochi",
        "species": "Dog",
        "breed": "French Bulldog",
        "image": "french-bulldog.jpg",
        "age_years": 2,
        "weight_lbs": 24,
        "gender": "male_neutered",
        "energy_level": "medium",
        "temperament": "friendly",
        "training_level": "basic",
        "good_with_cats": True,
        "location": "Downtown Ithaca",
        "latitude": 42.4410,
        "longitude": -76.4990,
        "bio": "Demo pup! Frenchie, hoodie enthusiast, and professional couch tester. Say hi in the chat.",
        "caption": "New hoodie, who dis? #frenchie",
    },
    {
        "owner": "demo",
        "name": "Ginger",
        "species": "Cat",
        "breed": "Orange Tabby",
        "image": "orange-cat-standing.jpg",
        "age_years": 4,
        "weight_lbs": 11,
        "gender": "female_spayed",
        "energy_level": "medium",
        "temperament": "calm",
        "good_with_dogs": True,
        "good_with_cats": True,
        "location": "Downtown Ithaca",
        "latitude": 42.4402,
        "longitude": -76.4978,
        "bio": "Mochi's roommate. Tolerates the dog. Loves sunbeams and the 5pm treat alarm.",
        "caption": "Strutting into the weekend like. #orangecat",
    },
]

FOLLOWS = {
    "demo": ["Buddy", "Luna", "Pepper", "Max", "Leo", "Scout"],
    "alexchen": ["Luna", "Pepper", "Mochi", "Scout"],
    "sarahk": ["Buddy", "Daisy", "Max", "Mochi"],
    "mikebrown": ["Buddy", "Leo", "Ginger"],
    "emilyw": ["Daisy", "Bear", "Mochi"],
}

REVIEWS = [
    (
        "Buddy",
        "sarahk",
        "playdate",
        5,
        "Buddy was so gentle with Pepper. Perfect big-brother energy.",
    ),
    ("Buddy", "emilyw", "walker", 5, "Walks beautifully on a leash and loves everyone he meets."),
    ("Luna", "alexchen", "sitter", 4, "Took a day to warm up, then she was on my lap all evening."),
    (
        "Mochi",
        "alexchen",
        "playdate",
        5,
        "Mochi and Daisy played tug for an hour. Total sweetheart.",
    ),
]

CONVERSATIONS = [
    (
        "demo",
        "alexchen",
        [
            ("alexchen", "Hi! Daisy would love a playdate with Mochi this weekend."),
            ("demo", "Mochi is in! Saturday morning at Stewart Park?"),
            ("alexchen", "Perfect, see you at 10. Bringing the good tennis balls."),
        ],
    ),
    (
        "demo",
        "sarahk",
        [("sarahk", "Pepper just learned 'sit'! Want to join puppy class next week?")],
    ),
]


class Command(BaseCommand):
    help = "Seed demo users, pets, posts, reviews, and conversations (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        users = self._users()
        pets = self._pets(users)
        self._posts(pets, users)
        self._follows(users, pets)
        self._reviews(users, pets)
        self._conversations(users)
        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write("Log in with the 'Try the live demo' button.")

    def _users(self):
        users = {}
        for data in USERS:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "name": data["name"],
                    "email": f"{data['username']}@example.com",
                    "location": data["location"],
                    "email_verified": data.get("email_verified", False),
                    "id_verified": data.get("id_verified", False),
                    "response_rate": 95,
                },
            )
            if created:
                user.set_password(SAMPLE_PASSWORD)
                user.save(update_fields=["password"])
                self.stdout.write(f"  user {user.username}")
            users[user.username] = user

        demo, created = User.objects.get_or_create(
            username=settings.DEMO_USERNAME,
            defaults={
                "name": "Demo Visitor",
                "email": "demo@example.com",
                "location": "Downtown Ithaca",
                "bio": "This is a shared demo account. Feel free to post, follow, and chat!",
                "email_verified": True,
                "response_rate": 100,
            },
        )
        if created:
            demo.set_unusable_password()
            demo.save(update_fields=["password"])
            self.stdout.write(f"  demo user {demo.username}")
        users["demo"] = demo
        return users

    def _pets(self, users):
        pets = {}
        for data in PETS:
            data = dict(data)
            owner = users[data.pop("owner")]
            image = data.pop("image")
            data.pop("caption")
            pet, created = Pet.objects.get_or_create(owner=owner, name=data["name"], defaults=data)
            if not pet.picture:
                with (IMAGES_DIR / image).open("rb") as handle:
                    pet.picture.save(image, File(handle), save=True)
            if created:
                self.stdout.write(f"  pet {pet.name}")
            pets[pet.name] = pet
        return pets

    def _posts(self, pets, users):
        now = timezone.now()
        for index, data in enumerate(PETS):
            pet = pets[data["name"]]
            if pet.posts.exists():
                continue
            post = Post(
                pet=pet, caption=data["caption"], created_at=now - timedelta(hours=3 * index + 1)
            )
            with (IMAGES_DIR / data["image"]).open("rb") as handle:
                post.image.save(data["image"], File(handle), save=True)
            for username in list(users)[index % 3 : index % 3 + 2]:
                PostLike.objects.get_or_create(user=users[username], post=post)
            if index % 2 == 0:
                commenter = users["sarahk" if pet.owner.username != "sarahk" else "alexchen"]
                Comment.objects.create(
                    user=commenter, post=post, content="So cute! Playdate soon? 🐾"
                )

    def _follows(self, users, pets):
        for username, pet_names in FOLLOWS.items():
            for name in pet_names:
                Follow.objects.get_or_create(follower=users[username], pet=pets[name])

    def _reviews(self, users, pets):
        for pet_name, reviewer, review_type, rating, content in REVIEWS:
            Review.objects.get_or_create(
                pet=pets[pet_name],
                reviewer=users[reviewer],
                defaults={"review_type": review_type, "rating": rating, "content": content},
            )

    def _conversations(self, users):
        now = timezone.now()
        for first, second, lines in CONVERSATIONS:
            exists = (
                Conversation.objects.filter(participants=users[first])
                .filter(participants=users[second])
                .exists()
            )
            if exists:
                continue
            conversation = Conversation.objects.create()
            conversation.participants.add(users[first], users[second])
            for offset, (sender, content) in enumerate(lines):
                sent_at = now - timedelta(minutes=10 * (len(lines) - offset))
                Message.objects.create(
                    conversation=conversation,
                    sender=users[sender],
                    content=content,
                    sent_at=sent_at,
                    read_at=sent_at if sender == "demo" or offset < len(lines) - 1 else None,
                )
