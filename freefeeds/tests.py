import datetime

from django.test import TestCase
from django.test import Client

import responses

from .models import Post, User


class PostTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client(HTTP_AUTHORIZATION="Bearer test")
        responses.reset()
        return super().setUp()

    @responses.activate
    def test_create_post(self):
        responses.add(
            responses.POST,
            "https://mokum.place/api/v1/posts.json",
            match=[lambda l: True],
            json={
                "post": {
                    "id": 0,
                    "text": "FOO",
                    "published_at": "2018-10-27",
                    "timelines": ["user"],
                    "comments_disabled": False,
                    "linebeaks": False,
                    "can_comment": False,
                    "attachments": [],
                    "comments_count": 0,
                    "likes": [],
                    "more_likes": 0,
                    "my_change": True,
                }
            },
            status=200,
        )
        responses.add(
            responses.GET,
            "https://mokum.place/user.json",
            json={
                "river": {
                    "current_user_name": "ravli",
                },
                "users": {
                    "9457": {
                        "id": 9457,
                        "name": "ravli",
                        "display_name": "всяко котило",
                        "created_at": "2018-10-27",
                        "avatar": {},
                        "avatar_url": "https://www.gravatar.com/avatar/cfdc7b38067740c7c38c82e77d2f161d?s=100&r=x&d=retro",
                    }
                },
            },
            status=200,
        )

        r = self.client.post("/api/v1/statuses", {"status": "FOO"})
        self.assertEqual(r.status_code, 200)

    @responses.activate
    def test_create_comment(self):
        u = User.objects.create(
            feed_id=1,
            username="tester",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        Post.objects.create(feed_id=1, user_id=u.pk, created_at=datetime.datetime.now())

        responses.add(
            responses.POST,
            "https://mokum.place/api/v1/posts/tester/1/comments.json",
            match=[lambda l: True],
            json={
                "user_id": 9457,
                "text": "Тест",
                "created_at": "2021-08-23T19:51:47.000Z",
                "updated_at": "2021-08-23T19:51:47.000Z",
                "post_id": 2835471,
                "entries": {},
                "realm": 0,
                "external_id": None,
                "id": 35866491
            },
            status=200,
        )
        responses.add(
            responses.GET,
            "https://mokum.place/user.json",
            json={
                "river": {
                    "current_user_name": "ravli",
                },
                "users": {
                    "9457": {
                        "id": 9457,
                        "name": "ravli",
                        "display_name": "всяко котило",
                        "created_at": "2018-10-27",
                        "avatar": {},
                        "avatar_url": "https://www.gravatar.com/avatar/cfdc7b38067740c7c38c82e77d2f161d?s=100&r=x&d=retro",
                    }
                },
            },
            status=200,
        )

        r = self.client.post("/api/v1/statuses", {"status": "FOO", "in_reply_to_id": 1})
        self.assertEqual(r.status_code, 200)
