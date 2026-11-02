import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from accounts.models import User
from feed.models import Post
from pets.models import Pet

PASSWORD = "correct-horse-battery-staple"

PET_DEFAULTS = {
    "species": "Dog",
    "breed": "Mutt",
    "bio": "A very good pet.",
    "gender": "male",
    "energy_level": "medium",
    "temperament": "friendly",
    "training_level": "basic",
    "social_preference": "groups",
    "location": "Ithaca, NY",
    "latitude": 42.4440,
    "longitude": -76.5019,
}


@pytest.fixture
def image_file():
    def make(name="photo.jpg"):
        buffer = io.BytesIO()
        Image.new("RGB", (8, 8), "orange").save(buffer, "JPEG")
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")

    return make


@pytest.fixture
def make_user(db):
    def make(username="owner", **extra):
        return User.objects.create_user(
            username=username, email=f"{username}@example.com", password=PASSWORD, **extra
        )

    return make


@pytest.fixture
def make_pet(make_user):
    counter = {"n": 0}

    def make(owner=None, name="Rex", **fields):
        counter["n"] += 1
        owner = owner or make_user(f"owner{counter['n']}")
        return Pet.objects.create(owner=owner, name=name, **{**PET_DEFAULTS, **fields})

    return make


@pytest.fixture
def make_post(make_pet, image_file):
    def make(pet=None, caption="Hello!"):
        return Post.objects.create(pet=pet or make_pet(), image=image_file(), caption=caption)

    return make


@pytest.fixture
def user(make_user):
    return make_user("alice")


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client
