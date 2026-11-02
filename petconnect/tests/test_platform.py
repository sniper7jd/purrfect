import cloudinary
import pytest
from django.core.management import call_command
from django.urls import reverse

from accounts.models import User
from chat.models import Message
from feed.models import Post
from petconnect.storage import CloudinaryMediaStorage
from pets.models import Pet
from pets.templatetags.media_tags import resized

pytestmark = pytest.mark.django_db


def test_cloudinary_urls_are_optimized():
    cloudinary.config(cloud_name="demo-cloud")
    url = CloudinaryMediaStorage().resized_url("petconnect/pets/abc123", 96)
    assert url.startswith("https://res.cloudinary.com/demo-cloud/image/upload/")
    for transform in ("c_limit", "f_auto", "q_auto", "w_96"):
        assert transform in url
    assert url.endswith("/petconnect/pets/abc123")


def test_resized_filter_falls_back_to_regular_url(make_pet, image_file):
    pet = make_pet()
    pet.picture.save("pic.jpg", image_file(), save=True)
    assert resized(pet.picture, 96) == pet.picture.url
    assert resized(None, 96) == ""


def test_seed_data_is_idempotent(settings):
    call_command("seed_data")
    counts = (
        User.objects.count(),
        Pet.objects.count(),
        Post.objects.count(),
        Message.objects.count(),
    )
    call_command("seed_data")

    assert counts == (
        User.objects.count(),
        Pet.objects.count(),
        Post.objects.count(),
        Message.objects.count(),
    )
    demo = User.objects.get(username=settings.DEMO_USERNAME)
    assert not demo.has_usable_password()
    assert demo.pets.count() == 2
    assert all(pet.picture for pet in Pet.objects.all())


def test_service_worker_and_offline_page(client):
    response = client.get("/sw.js")
    assert response.status_code == 200
    assert response["Content-Type"] == "application/javascript"
    assert "no-cache" in response["Cache-Control"]
    assert client.get(reverse("offline")).status_code == 200


def test_production_settings_require_secret_key(monkeypatch):
    import importlib

    from django.core.exceptions import ImproperlyConfigured

    import petconnect.settings as settings_module

    monkeypatch.setenv("DEBUG", "False")
    monkeypatch.setenv("SECRET_KEY", "")
    with pytest.raises(ImproperlyConfigured):
        importlib.reload(settings_module)
    monkeypatch.setenv("SECRET_KEY", "restored")
    importlib.reload(settings_module)
