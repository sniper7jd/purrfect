import pytest
from django.urls import reverse

from accounts.models import User

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db


def test_register_logs_in_and_sends_user_to_add_pet(client):
    response = client.post(
        reverse("accounts:register"),
        {
            "name": "New Person",
            "username": "newbie",
            "email": "newbie@example.com",
            "password1": PASSWORD,
            "password2": PASSWORD,
        },
    )
    assert response.status_code == 302
    assert response.url == reverse("pets:add")
    assert User.objects.get(username="newbie").name == "New Person"
    assert "_auth_user_id" in client.session


def test_login_follows_internal_next(client, user):
    response = client.post(
        reverse("accounts:login") + "?next=/playdates/",
        {"username": user.username, "password": PASSWORD, "next": "/playdates/"},
    )
    assert response.status_code == 302
    assert response.url == "/playdates/"


def test_login_ignores_external_next(client, user):
    response = client.post(
        reverse("accounts:login"),
        {"username": user.username, "password": PASSWORD, "next": "https://evil.example/"},
    )
    assert response.status_code == 302
    assert response.url == reverse("feed:home")


def test_logout_requires_post(auth_client):
    assert auth_client.get(reverse("accounts:logout")).status_code == 405
    assert auth_client.post(reverse("accounts:logout")).status_code == 302
    assert "_auth_user_id" not in auth_client.session


def test_demo_login_signs_in_demo_account(client, make_user, settings):
    demo = make_user(settings.DEMO_USERNAME)
    demo.set_unusable_password()
    demo.save()

    response = client.post(reverse("accounts:demo_login"))

    assert response.status_code == 302
    assert response.url == reverse("feed:home")
    assert client.session["_auth_user_id"] == str(demo.pk)


def test_demo_login_can_be_disabled(client, make_user, settings):
    make_user(settings.DEMO_USERNAME)
    settings.DEMO_LOGIN_ENABLED = False

    response = client.post(reverse("accounts:demo_login"))

    assert response.url == reverse("accounts:login")
    assert "_auth_user_id" not in client.session


def test_demo_login_is_post_only(client):
    assert client.get(reverse("accounts:demo_login")).status_code == 405


def test_profile_counts_followers_across_pets(auth_client, make_pet, make_user, user):
    from pets.models import Follow

    first, second = make_pet(owner=user, name="A"), make_pet(owner=user, name="B")
    for name in ("x", "y"):
        Follow.objects.create(follower=make_user(name), pet=first)
    Follow.objects.create(follower=User.objects.get(username="x"), pet=second)

    response = auth_client.get(reverse("accounts:profile", args=[user.username]))

    assert response.context["follower_total"] == 3
