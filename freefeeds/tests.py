from django.test import TestCase
from django.test import Client

import responses


class PostTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client(HTTP_AUTHORIZATION="Bearer test")
        return super().setUp()

    @responses.activate
    def test_create_post(self):
        responses.add(
            responses.POST, 
            'https://mokum.place/api/v1/posts.json',
            match=[
                lambda l: True
            ],
            json={
                "entries": {
                    "{river_uuid}": {
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
                            "my_change": True
                        }
                    }
                }
            }, status=200
        )
        responses.add(
            responses.GET, 
            'https://mokum.place/user.json',
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
                }
            }, status=200
        )

        r = self.client.post("/api/v1/statuses", {"status": "FOO"})
        self.assertEqual(r.status_code, 200)