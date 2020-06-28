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

    NEW_POST_URL = HOST + "api/v1/posts.json"
    NEW_COMMENT_URL = HOST + "api/v1/posts/%s/%s/comments.json"
    NEW_ATTACHMENT_URL = HOST + "v1/attachments"

    ME_URL = HOST + "/index.json"

    POST_LIKE_URL = HOST + "v1/posts/%s/%s/favs.json"
    COMMENT_LIKE_URL = HOST + "api/v1/posts/%s/%s/clike/%s.json"

    def __init__(self, app_key):
        if not app_key:
            raise RuntimeError("App key is invalid")
        self.app_key = app_key
        
    @staticmethod
    def from_request(request):
        return Client(request.META["HTTP_AUTHORIZATION"].replace("Bearer ", ""))
        
    def get_headers(self):
        return {
          "X-API-Token": self.app_key
        }
    
    def request(self, url, method="GET", data=None, **kwargs):
        if settings.DEBUG:
            print(method + ": " + url)
        result = requests.request(method, url, headers=self.get_headers(), json=data, **kwargs).json()
        return result
    
    def get_me(self):
        data = self.request(self.HOME_URL)
        if settings.DEBUG:
            print(data.keys())
            print(data)

        username = data["river"]["current_user_name"]
        user_data = [u for u in data["users"] if u["name"] == username][0]
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
        posts = [Post.from_feed_json(p, ff_data["users"]) for p in ff_data["entries"]]
        
        return posts
    
    def get_post(self, md_id):
        md_post = Post.objects.get(pk=md_id)
        ff_data = self.request(self.POSTS_URL % (md_post.user.username, md_post.feed_id))
        post = Post.from_feed_json(ff_data["entries"], ff_data["users"])
        
        comments = [Post.from_feed_comment_json(post, c, ff_data["users"]) for c in ff_data["entries"][0]["comments"]]
        return [post] + comments
    
    def get_notifications(self):
        # TODO
        return []
    
    def get_user_timeline(self, md_id, limit=120, max_id=None, since_id=None):
        md_user = User.objects.get(pk=md_id)
        return self.get_feed(self.USER_FEED_URL % md_user.username, limit, max_id, since_id)

    def post_like(self, md_id):
        post = Post.objects.get(pk=md_id)
    
        if post.parent is not None:
            self.request(self.COMMENT_LIKE_URL % post.feed_id, method="POST")
            comments = self.get_post(post.parent_id)[1:]
            comment = [p for p in comments if p.id == md_id][0]
            return comment
        else:
            self.request(self.POST_LIKE_URL % post.feed_id, method="POST")
            return self.get_post(md_id)[0]

    def post_unlike(self, md_id):
        post = Post.objects.get(pk=md_id)
    
        if post.parent is not None:
            self.request(self.COMMENT_UNLIKE_URL % post.feed_id, method="POST")
        else:
            self.request(self.POST_UNLIKE_URL % post.feed_id, method="POST")
        return self.get_post(md_id)[0]

    def new_post_or_comment(self, md_data):
        reply_id = md_data.get("in_reply_to_id", None)
        if reply_id is not None:
            post = Post.objects.get(pk=reply_id)
            
            if post.parent:
                postId = post.parent.feed_id
            else:
                postId = post.feed_id
                
            feed_data = {
                "comment": {
                    "body": md_data["status"] or '.',
                    "postId": postId
                }
            }

            new_comment = self.request(self.NEW_COMMENT_URL, method="POST", data=feed_data)
            new_md_post = Post.from_feed_comment_json(post, new_comment["comments"], new_comment["users"])
        else:
            feed_data = {
                "post": {
                    "body": md_data["status"] or '.',
                    "attachments": [Attachment.objects.get(pk=aid).feed_id for aid in md_data.getlist("media_ids[]")]
                },
                "meta": {
                    "commentsDisabled": False,
                    "feeds": [self.get_me().username]
                }
            }
    
            new_post = self.request(self.NEW_POST_URL, method="POST", data=feed_data)
            new_md_post = Post.from_feed_json(new_post["posts"], new_post["users"])
        
        return new_md_post
    
    def new_attachment(self, md_file):
        result = self.request(self.NEW_ATTACHMENT_URL, method="POST", files={"file": md_file})
        return Attachment.from_feed_json(None, result['attachments'])