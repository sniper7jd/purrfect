import pytest
from django.urls import reverse

from pets.models import Follow, Pet

from .conftest import PET_DEFAULTS

pytestmark = pytest.mark.django_db


def pet_form_data(**overrides):
    data = {
        **{k: v for k, v in PET_DEFAULTS.items() if k not in {"latitude", "longitude"}},
        "name": "Biscuit",
        "age_years": 2,
        "age_months": 0,
        "available_for_playdate": "on",
        "latitude": "42.4440",
        "longitude": "-76.5019",
    }
    data.update(overrides)
    return data


def test_create_pet_saves_coordinates(auth_client, user):
    response = auth_client.post(reverse("pets:add"), pet_form_data())

    pet = Pet.objects.get(name="Biscuit")
    assert response.status_code == 302
    assert pet.owner == user
    assert pet.latitude == pytest.approx(42.444)
    assert pet.longitude == pytest.approx(-76.5019)


def test_create_pet_without_coordinates_is_allowed(auth_client):
    auth_client.post(reverse("pets:add"), pet_form_data(latitude="", longitude=""))
    assert Pet.objects.get(name="Biscuit").latitude is None


@pytest.mark.parametrize(
    ("lat", "lng"),
    [("42.44", ""), ("123", "-76.5")],
)
def test_create_pet_rejects_invalid_coordinates(auth_client, lat, lng):
    response = auth_client.post(reverse("pets:add"), pet_form_data(latitude=lat, longitude=lng))
    assert response.status_code == 200
    assert not Pet.objects.filter(name="Biscuit").exists()


def test_only_owner_can_edit(auth_client, make_pet):
    other_pet = make_pet()
    assert auth_client.get(reverse("pets:edit", args=[other_pet.id])).status_code == 404


def test_follow_with_htmx_returns_button_and_count(auth_client, make_pet, user):
    pet = make_pet()
    response = auth_client.post(reverse("pets:follow", args=[pet.id]), HTTP_HX_REQUEST="true")

    body = response.content.decode()
    assert Follow.objects.filter(follower=user, pet=pet).exists()
    assert "Following" in body
    assert 'id="follower-count" hx-swap-oob="true">1<' in body


def test_unfollow(auth_client, make_pet, user):
    pet = make_pet()
    Follow.objects.create(follower=user, pet=pet)
    auth_client.post(reverse("pets:unfollow", args=[pet.id]))
    assert not Follow.objects.filter(follower=user, pet=pet).exists()


def test_cannot_follow_own_pet(auth_client, make_pet, user):
    pet = make_pet(owner=user)
    assert auth_client.post(reverse("pets:follow", args=[pet.id])).status_code == 400


def test_profile_query_count_is_constant(
    client, make_pet, make_post, make_user, django_assert_max_num_queries
):
    pet = make_pet()
    for i in range(5):
        make_post(pet=pet)
        Follow.objects.create(follower=make_user(f"fan{i}"), pet=pet)

    with django_assert_max_num_queries(5):
        response = client.get(reverse("pets:profile", args=[pet.id]))
    assert response.context["pet"].posts_total == 5
    assert response.context["pet"].followers_total == 5


@pytest.mark.parametrize("name", ["delete", "add_review", "all_reviews"])
def test_previously_missing_templates_render(auth_client, make_pet, user, name):
    pet = make_pet(owner=user) if name == "delete" else make_pet()
    assert auth_client.get(reverse(f"pets:{name}", args=[pet.id])).status_code == 200
