import pytest
from django.urls import reverse

from playdates.views import MAX_MATCH_SCORE, distance_km, ranked_matches

pytestmark = pytest.mark.django_db

ITHACA = (42.4440, -76.5019)


def test_distance_km_ithaca_to_nyc():
    assert distance_km(*ITHACA, 40.7128, -74.0060) == pytest.approx(300, abs=20)


def test_ranked_matches_orders_by_compatibility(make_pet, user):
    mine = make_pet(owner=user, name="Mine", energy_level="high", temperament="playful")
    best = make_pet(
        name="Best",
        energy_level="high",
        temperament="playful",
        training_level="basic",
        vaccinations_current=True,
        latitude=ITHACA[0] + 0.01,
        longitude=ITHACA[1],
    )
    okay = make_pet(
        name="Okay", energy_level="medium", temperament="calm", latitude=43.5, longitude=-75.0
    )
    far_mismatch = make_pet(
        name="Far",
        energy_level="low",
        temperament="shy",
        social_preference="slow_intro",
        training_level="none",
        latitude=40.7,
        longitude=-74.0,
    )

    matches = ranked_matches(mine)

    assert [pet.name for pet in matches] == ["Best", "Okay", "Far"]
    assert matches[0].match_score == MAX_MATCH_SCORE
    assert matches[0].match_percent == 100
    assert matches[0].distance_km == pytest.approx(1.1, abs=0.2)
    assert matches[1].match_score > matches[2].match_score
    assert {best.id, okay.id, far_mismatch.id} == {pet.id for pet in matches}


def test_ranked_matches_hard_filters(make_pet, user):
    mine = make_pet(owner=user, name="Mine")
    make_pet(owner=user, name="AlsoMine")
    make_pet(name="Cat", species="Cat")
    make_pet(name="Busy", available_for_playdate=False)
    make_pet(name="Grumpy", good_with_dogs=False)
    make_pet(name="Inactive", is_active=False)
    keeper = make_pet(name="Keeper")

    assert [pet.id for pet in ranked_matches(mine)] == [keeper.id]


def test_ranked_matches_without_coordinates(make_pet, user):
    mine = make_pet(owner=user, name="Mine", latitude=None, longitude=None)
    other = make_pet(name="Other")
    matches = ranked_matches(mine)
    assert matches[0].id == other.id
    assert matches[0].distance_km is None


def test_smart_match_view(auth_client, make_pet, user):
    make_pet(owner=user, name="Mine")
    make_pet(name="Friend")
    response = auth_client.get(reverse("playdates:smart_match"))
    body = response.content.decode()
    assert "Friend" in body
    assert "% match" in body


def test_smart_match_requires_login(client):
    response = client.get(reverse("playdates:smart_match"))
    assert response.status_code == 302


def test_map_pets_filters_by_bounds(client, make_pet):
    inside = make_pet(name="Inside")
    make_pet(name="Outside", latitude=40.7, longitude=-74.0)
    make_pet(name="Unknown", latitude=None, longitude=None)

    response = client.get(
        reverse("playdates:map_pets"),
        {"south": 42.0, "north": 43.0, "west": -77.0, "east": -76.0},
    )

    data = response.json()
    assert [pet["id"] for pet in data["pets"]] == [inside.id]
    assert data["truncated"] is False
    assert data["pets"][0]["profile_url"] == inside.get_absolute_url()


def test_map_pets_caps_results(client, make_pet, settings):
    settings.MAP_MAX_PETS = 1
    make_pet(name="One")
    make_pet(name="Two")
    data = client.get(
        reverse("playdates:map_pets"), {"south": 42, "north": 43, "west": -77, "east": -76}
    ).json()
    assert len(data["pets"]) == 1
    assert data["truncated"] is True


def test_map_pets_requires_bounds(client):
    assert client.get(reverse("playdates:map_pets")).status_code == 400


def test_map_page_embeds_config_safely(client, make_pet):
    pet = make_pet(name='</script><script>alert("x")</script>')
    response = client.get(reverse("playdates:map") + f"?pet={pet.id}")
    body = response.content.decode()
    assert '<script>alert("x")' not in body
    assert response.context["map_config"]["focusPetId"] == pet.id


def test_suggest_returns_matches(client, make_pet):
    make_pet(name="Goldie", breed="Golden Retriever")
    data = client.get(reverse("playdates:suggest"), {"query": "gold"}).json()
    assert {"text": "Goldie", "type": "name"} in data
    assert {"text": "Golden Retriever", "type": "breed"} in data
