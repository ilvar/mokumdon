import re

import arrow
from django.db import models


class FfToMdConvertorMixin:
    @staticmethod
    def dt_from_frf(frf_dt):
        return frf_dt

    @staticmethod
    def dt_to_md(dt):
        return arrow.get(dt).format("YYYY-MM-DDTHH:mm:ss.SSS") + "Z"


class User(models.Model, FfToMdConvertorMixin):
    feed_id = models.CharField(max_length=100, db_index=True)
    username = models.CharField(max_length=100)
    screen_name = models.CharField(max_length=100)
    avatar_url = models.URLField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    @staticmethod
    def from_feed_json(ff_user):
        try:
            return User.objects.get(feed_id=ff_user["id"])
        except User.DoesNotExist:
            return User.objects.create(
                feed_id=ff_user["id"],
                username=ff_user["name"],
                screen_name=ff_user["display_name"],
                avatar_url=ff_user["avatar_url"],
                created_at=User.dt_from_frf(ff_user["created_at"]),
                updated_at=User.dt_from_frf(ff_user["created_at"]),
            )

    def to_md_json(self):
        return {
            "id": self.pk,
            "username": self.username,
            "acct": "%s" % self.username,
            "display_name": self.screen_name,
            "locked": False,
            "created_at": User.dt_to_md(self.created_at),
            "followers_count": 0,
            "following_count": 0,
            "statuses_count": 0,
            "note": "",
            "uri": "https://mokum.place/%s" % self.username,
            "url": "https://mokum.place/%s" % self.username,
            "avatar": self.avatar_url,
            "avatar_static": self.avatar_url,
            "header": "",
            "header_static": "",
            "emojis": [],
            "bot": False,
        }


class Post(models.Model, FfToMdConvertorMixin):
    feed_id = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(null=True)

    @staticmethod
    def from_feed_json(ff_post, all_ff_users):
        try:
            md_post = Post.objects.get(feed_id=ff_post["id"], parent__isnull=True)
        except Post.DoesNotExist:
            ff_user = [u for u in all_ff_users if u["id"] == ff_post["user_id"]][0]
            md_user = User.from_feed_json(ff_user)
            md_post = Post.objects.create(
                feed_id=ff_post["id"],
                parent=None,
                user=md_user,
                created_at=Post.dt_from_frf(ff_post["published_at"]),
            )

        md_post.data = dict(
            body=ff_post["text"],
            likes=len(ff_post["likes"]) + ff_post["more_likes"],
            comments=ff_post["comments_count"],
            comments_disabled=not ff_post["can_comment"],
            updated_at=Post.dt_from_frf(ff_post["published_at"]),
        )

        md_post.attachments = []

        for ff_attachment in ff_post["attachments"]:
            md_post.attachments.append(
                Attachment.from_feed_json(md_post, ff_attachment)
            )

        return md_post

    @staticmethod
    def from_feed_comment_json(parent_post, ff_comment, all_ff_users):
        try:
            md_post = Post.objects.get(feed_id=ff_comment["id"])
        except Post.DoesNotExist:
            ff_user = [u for u in all_ff_users if u["id"] == ff_comment["user_id"]][0]
            md_user = User.from_feed_json(ff_user)
            md_post = Post.objects.create(
                feed_id=ff_comment["id"],
                parent=parent_post,
                user=md_user,
                created_at=Post.dt_from_frf(
                    ff_comment.get("created_at", ff_comment.get("published_at"))
                ),
            )

        md_post.attachments = []

        md_post.data = dict(
            body=ff_comment["text"],
            likes=ff_comment.get("clikes_count", 0),
            comments=0,
            comments_disabled=False,
            updated_at=Post.dt_from_frf(
                ff_comment.get("created_at", ff_comment.get("published_at"))
            ),
        )

        return md_post

    def get_absolute_url(self):
        if self.parent is not None:
            return "https://mokum.place/%s/%s" % (
                self.parent.user.username,
                self.parent.feed_id,
            )
        else:
            return "https://mokum.place/%s/%s" % (self.user.username, self.feed_id)

    def to_md_json(self):
        return {
            "id": self.pk,
            "uri": self.get_absolute_url(),
            "url": self.get_absolute_url(),
            "account": self.user.to_md_json(),
            "content": self.data["body"],
            "created_at": Post.dt_to_md(self.created_at),
            "emojis": [],
            "replies_count": self.data["comments"],
            "reblogs_count": self.data["comments"],
            "favourites_count": self.data["likes"],
            "sensitive": False,
            "reblog": None,
            "in_reply_to_id": None,
            "spoiler_text": "",
            "visibility": "public",
            "media_attachments": [a.to_md_json() for a in self.attachments],
            "mentions": [],
            "tags": [],
            "application": {"name": "Mokum"},
            "language": "ru",  # TODO
            "pinned": False,
        }


class Attachment(models.Model, FfToMdConvertorMixin):
    feed_id = models.CharField(max_length=100, db_index=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)

    @staticmethod
    def from_feed_json(md_post, ff_attachment):
        try:
            att = Attachment.objects.get(feed_id=ff_attachment["id"])
            if att.post is None and md_post is not None:
                att.post = md_post
                att.save()
        except Attachment.DoesNotExist:
            att = Attachment.objects.create(feed_id=ff_attachment["id"], post=md_post)

        att.data = dict(
            media_type="image",
            url="https://mokum.place" + ff_attachment["medium_url"],
            thumbnail_url="https://mokum.place" + ff_attachment["thumb_url"],
            width=ff_attachment["original_width"],
            height=ff_attachment["original_height"],
        )
        return att

    def to_md_json(self):
        return {
            "id": self.pk,
            "type": self.data["media_type"],
            "url": self.media_url(self.data["url"]),
            "remote_url": self.media_url(self.data["url"]),
            "preview_url": self.media_url(self.data["thumbnail_url"]),
            "text_url": "",
            "meta": (self.data["width"] and self.data["height"])
            and {"width": self.data["width"], "height": self.data["height"]}
            or {},
            "description": "",
        }

    def media_url(self, mokum_url):
        redirect_url = re.sub("^https://mokum.place/", "https://mokumdon.rkd.pw/media/", mokum_url)
        return redirect_url