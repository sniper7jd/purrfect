import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from feed.models import Comment, PostLike
from pets.models import Follow

pytestmark = pytest.mark.django_db


def test_landing_page_for_visitors(client, make_pet):
    make_pet(name="Famous")
    response = client.get(reverse("feed:home"))
    assert response.status_code == 200
    assert "Try the live demo" in response.content.decode()
    assert "Famous" in response.content.decode()


def _feed_queries(client):
    with CaptureQueriesContext(connection) as queries:
        assert client.get(reverse("feed:home")).status_code == 200
    return len(queries)


def test_feed_query_count_does_not_grow_with_posts(
    auth_client, user, make_pet, make_post, make_user
):
    pet = make_pet()
    Follow.objects.create(follower=user, pet=pet)
    make_post(pet=pet)
    baseline = _feed_queries(auth_client)

    for i in range(8):
        post = make_post(pet=pet)
        PostLike.objects.create(user=make_user(f"liker{i}"), post=post)
        Comment.objects.create(user=user, post=post, content="cute")

    assert _feed_queries(auth_client) == baseline


def test_feed_paginates_with_htmx_infinite_scroll(auth_client, user, make_pet, make_post, settings):
    settings.POSTS_PER_PAGE = 3
    pet = make_pet()
    Follow.objects.create(follower=user, pet=pet)
    for _ in range(5):
        make_post(pet=pet)

    first = auth_client.get(reverse("feed:home")).content.decode()
    assert first.count("<article") == 3
    assert 'hx-get="/?page=2"' in first

    second = auth_client.get(reverse("feed:home") + "?page=2", HTTP_HX_REQUEST="true")
    body = second.content.decode()
    assert "<html" not in body
    assert body.count("<article") == 2
    assert "hx-get" not in body


def test_like_toggles_and_returns_partial(auth_client, user, make_post):
    post = make_post()
    url = reverse("feed:like_post", args=[post.id])

    liked = auth_client.post(url, HTTP_HX_REQUEST="true").content.decode()
    assert PostLike.objects.filter(user=user, post=post).exists()
    assert "1 like" in liked
    assert 'aria-pressed="true"' in liked

    unliked = auth_client.post(url, HTTP_HX_REQUEST="true").content.decode()
    assert not PostLike.objects.filter(user=user, post=post).exists()
    assert "0 likes" in unliked


def test_comment_with_htmx_returns_comment_partial(auth_client, make_post):
    post = make_post()
    response = auth_client.post(
        reverse("feed:add_comment", args=[post.id]),
        {"content": "<b>so cute</b>"},
        HTTP_HX_REQUEST="true",
    )
    body = response.content.decode()
    assert "&lt;b&gt;so cute&lt;/b&gt;" in body
    assert Comment.objects.get(post=post).content == "<b>so cute</b>"


def test_create_post(auth_client, user, make_pet, image_file):
    pet = make_pet(owner=user)
    response = auth_client.post(
        reverse("feed:create_post"),
        {"pet_id": pet.id, "caption": "first!", "image": image_file()},
    )
    assert response.status_code == 302
    assert pet.posts.get().caption == "first!"


def test_cannot_post_as_someone_elses_pet(auth_client, user, make_pet, image_file):
    make_pet(owner=user)
    response = auth_client.post(
        reverse("feed:create_post"),
        {"pet_id": make_pet().id, "caption": "nope", "image": image_file()},
    )
    assert response.status_code == 404


def test_story_flow(auth_client, user, make_pet, image_file):
    pet = make_pet(owner=user)
    assert auth_client.get(reverse("feed:create_story")).status_code == 200
    auth_client.post(reverse("feed:create_story"), {"pet_id": pet.id, "image": image_file()})
    story = pet.stories.get()
    assert auth_client.get(reverse("feed:view_story", args=[story.id])).status_code == 200
    assert story.views.filter(user=user).exists()
