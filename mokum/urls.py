from django.urls import include
from django.urls import path, re_path

import feed_auth.views
import freefeeds.views

urlpatterns = [
    path("oauth/authorize", feed_auth.views.oauth_authorize),
    path("oauth/token", feed_auth.views.oauth_token),
    path("oauth/", include("freefeeds.oauth2_urls", namespace="oauth2_provider")),
    path("api/", include("freefeeds.urls")),
    re_path(r"^media/(?P<path>.*)$", freefeeds.views.media_redirect),
    path(".well-known/nodeinfo", freefeeds.views.nodeinfo_v1),
    path("nodeinfo/2.0", freefeeds.views.nodeinfo_v2),
]
