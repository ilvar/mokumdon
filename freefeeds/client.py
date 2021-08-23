import urllib.parse

import requests
from django.conf import settings

from freefeeds.models import User, Post, Attachment


class Client:
    app_key = None

    HOST = "https://mokum.place"
    HOME_URL = HOST + "/index.json"
    USER_FEED_URL = HOST + "/%s.json"
    POSTS_URL = HOST + "/%s/%s.json"

    NEW_POST_URL = HOST + "/api/v1/posts.json"
    NEW_COMMENT_URL = HOST + "/api/v1/posts/%s/%s/comments.json"
    NEW_ATTACHMENT_URL = HOST + "/v1/attachments"

    ME_URL = HOST + "/user.json"

    POST_LIKE_URL = HOST + "/api/v1/posts/%s/%s/likes.json"
    COMMENT_LIKE_URL = HOST + "/api/v1/posts/%s/%s/clike/%s.json"

    def __init__(self, app_key):
        if not app_key:
            raise RuntimeError("App key is invalid")
        self.app_key = app_key

    @staticmethod
    def from_request(request):
        return Client(request.META["HTTP_AUTHORIZATION"].replace("Bearer ", ""))

    def get_headers(self):
        return {"X-API-Token": self.app_key}

    def request(self, url, method="GET", data=None, **kwargs):
        if settings.DEBUG:
            print(method + ": " + url)
        result = requests.request(
            method, url, headers=self.get_headers(), json=data, **kwargs
        ).json()
        return result

    def get_me(self):
        data = self.request(self.ME_URL)
        username = data["river"]["current_user_name"]
        user_data = [u for u in data["users"].values() if u["name"] == username][0]
        return User.from_feed_json(user_data)

    def get_home(self, limit=120, max_id=None, since_id=None):
        return self.get_feed(self.HOME_URL, limit, max_id, since_id)

    def get_feed(self, url, limit=120, max_id=None, since_id=None):
        if max_id is not None and max_id != 0:
            try:
                max_created_at = Post.objects.get(pk=max_id).created_at
            except Post.DoesNotExist:
                max_created_at = None
        else:
            max_created_at = None

        params = {}
        if max_created_at:
            params["start_from"] = max_created_at
        ff_data = self.request(url + "?" + urllib.parse.urlencode(params))
        posts = [
            Post.from_feed_json(p, ff_data["users"].values())
            for p in ff_data["entries"]
        ]

        return posts

    def get_post(self, md_id):
        md_post = Post.objects.get(pk=md_id)
        url = self.POSTS_URL % (md_post.user.username, md_post.feed_id)
        ff_data = self.request(url)
        post = Post.from_feed_json(ff_data["entries"][0], ff_data["users"].values())

        comments = [
            Post.from_feed_comment_json(post, c, ff_data["users"].values())
            for c in ff_data["entries"][0]["comments"]
        ]
        return [post] + comments

    def get_notifications(self):
        # TODO
        return []

    def get_user_timeline(self, md_id, limit=120, max_id=None, since_id=None):
        md_user = User.objects.get(pk=md_id)
        return self.get_feed(
            self.USER_FEED_URL % md_user.username, limit, max_id, since_id
        )

    def post_like(self, md_id):
        post = Post.objects.get(pk=md_id)

        if post.parent is not None:
            self.request(
                self.COMMENT_LIKE_URL % (post.user.username, post.feed_id, post.id),
                method="POST",
            )
            comments = self.get_post(post.parent_id)[1:]
            comment = [p for p in comments if p.id == md_id][0]
            return comment
        else:
            self.request(
                self.POST_LIKE_URL % (post.user.username, post.feed_id), method="POST"
            )
            return self.get_post(md_id)[0]

    def post_unlike(self, md_id):
        post = Post.objects.get(pk=md_id)

        if post.parent is not None:
            self.request(
                self.COMMENT_LIKE_URL % (post.user.username, post.feed_id, post.id),
                method="DELETE",
            )
        else:
            self.request(
                self.POST_LIKE_URL % (post.user.username, post.feed_id), method="DELETE"
            )
        return self.get_post(md_id)[0]

    def _get_post_from_response(self, response, user_id):
        response["post"]["user_id"] = user_id
        response["post"].setdefault("likes", [])
        response["post"].setdefault("attachments", [])
        response["post"].setdefault("more_likes", 0)
        response["post"].setdefault("comments_count", 0)
        response["post"].setdefault("can_comment", 0)
        return response

    def new_post_or_comment(self, md_data):
        reply_id = md_data.get("in_reply_to_id", None)
        if reply_id is not None:
            post = Post.objects.get(pk=reply_id)

            if post.parent:
                postId = post.parent.feed_id
                username = post.parent.user.username
            else:
                postId = post.feed_id
                username = post.user.username

            media_ids = [
                Attachment.objects.get(pk=aid).feed_id
                for aid in md_data.getlist("media_ids[]")
            ]

            feed_data = {
                "comment": {
                    "text": md_data["status"] or ".",
                    "attachment_id": media_ids and media_ids[0] or None,
                }
            }

            user_id = self.get_me().feed_id
            response = self.request(
                self.NEW_COMMENT_URL % (username, postId),
                method="POST",
                data=feed_data,
            )
            new_comment = self._get_post_from_response(
                {"post": response},
                user_id,
            )
            new_md_post = Post.from_feed_comment_json(
                post, new_comment["post"], [{"id": user_id}]
            )
        else:
            feed_data = {
                "post": {
                    "text": md_data["status"] or ".",
                    "attachment_ids": [
                        Attachment.objects.get(pk=aid).feed_id
                        for aid in md_data.getlist("media_ids[]")
                    ],
                    "linebreaks": True,
                    "timelines": ["user"],
                    "comments_disabled": False,
                }
            }

            user_id = self.get_me().feed_id
            response = self.request(self.NEW_POST_URL, method="POST", data=feed_data)
            new_post = self._get_post_from_response(response, user_id)
            new_md_post = Post.from_feed_json(new_post["post"], [{"id": user_id}])

        return new_md_post

    def new_attachment(self, md_file):
        result = self.request(
            self.NEW_ATTACHMENT_URL, method="POST", files={"file": md_file}
        )
        return Attachment.from_feed_json(None, result["attachments"])
