import datetime

from django.test import TestCase
from django.test import Client

import responses

from .models import Post, User


class PostTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client(HTTP_AUTHORIZATION="Bearer test")
        return super().setUp()

    @responses.activate
    def test_create_post(self):
        responses.reset()
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
        responses.reset()
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
                "id": 35866491,
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

    @responses.activate
    def test_user_timeline(self):
        responses.reset()
        u = User.objects.create(
            feed_id=1,
            username="tester",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        responses.add(
            responses.GET,
            "https://mokum.place/tester.json",
            json={
                "entries": [
                    {
                        "url": "/ravli/2835471",
                        "user_id": 9457,
                        "text": "А нам все равно",
                        "published_at": "2021-08-23T19:18:19.000Z",
                        "backlinks": [],
                        "status": "fyeo",
                        "can_comment": True,
                        "can_delete": True,
                        "can_edit": True,
                        "can_moderate": True,
                        "linebreaks": True,
                        "api_url": "/api/v1/posts/ravli/2835471",
                        "more_likes": 0,
                        "likes": [],
                        "fav_count": 0,
                        "can_fav": True,
                        "comments": [
                            {
                                "id": 35866617,
                                "post_id": 2835471,
                                "user_id": 9457,
                                "text": "Тест",
                                "created_at": "2021-08-23T20:01:57.000Z",
                                "api_url": "/api/v1/posts/ravli/2835471/comments/35866617",
                                "url": "/ravli/2835471#c35866617",
                                "can_edit": True,
                                "can_delete": True,
                            }
                        ],
                        "comments_count": 1,
                        "gap_position": 0,
                        "gap_clikes_count": 0,
                        "attachments": [],
                        "embeds": [],
                        "reason": {"user_fyeo": [9457]},
                        "timelines": ["user_fyeo"],
                        "fresh_at": "2021-08-23T20:01:57.000Z",
                        "version": 7,
                        "id": 2835471,
                    }
                ],
                "river": {
                    "uuid": "54d395cb-d510-4050-86c6-8e64882d3e1f",
                    "signature": "54d395cb-d510-4050-86c6-8e64882d3e1f/user:ravli",
                    "current_user_name": "ravli",
                    "timestamp": "2021-08-23T20:07:46.918Z",
                    "descriptor": "user:ravli",
                    "what": "user",
                },
                "users": {
                    "9457": {
                        "id": 9457,
                        "name": "ravli",
                        "display_name": "всяко котило",
                        "status": "public",
                        "description": "",
                        "created_at": "2018-10-27",
                        "url": "/ravli",
                        "avatar": {
                            "id": 0,
                            "user_id": 9457,
                            "attachment_file_name": "gravatar.jpg",
                            "updated_at": "2020-12-18T20:25:05+00:00",
                            "orientation": "portrait",
                            "uuid": "8e0f0e6f-d2c7-4aac-93d4-79d22aa3f317",
                            "position": 0,
                            "stage2_image_url_template": "https://www.gravatar.com/avatar/cfdc7b38067740c7c38c82e77d2f161d?s={w}&r=x&d=retro",
                            "stage1_image_url": "https://www.gravatar.com/avatar/cfdc7b38067740c7c38c82e77d2f161d?s=100&r=x&d=retro",
                            "original_url": "https://www.gravatar.com/avatar/cfdc7b38067740c7c38c82e77d2f161d?s=100&r=x&d=retro",
                            "original_width": 100,
                            "original_height": 100,
                        },
                        "avatar_width": 50,
                        "avatar_height": 50,
                        "avatar_url": "https://www.gravatar.com/avatar/cfdc7b38067740c7c38c82e77d2f161d?s=100&r=x&d=retro",
                        "counts": {},
                    }
                },
            },
            status=200,
        )

        r = self.client.get("/api/v1/accounts/1/statuses")
        self.assertEqual(r.status_code, 200)

        r = self.client.get("/api/v1/accounts/1")
        self.assertEqual(r.status_code, 200)
