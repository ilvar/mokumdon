from django.urls import path

from oauth2_provider import views


app_name = "oauth2_provider"


base_urlpatterns = [
    path(r"^authorize$", views.AuthorizationView.as_view(), name="authorize"),
    path(r"^token$", views.TokenView.as_view(), name="token"),
    path(r"^revoke_token$", views.RevokeTokenView.as_view(), name="revoke-token"),
    path(r"^introspect$", views.IntrospectTokenView.as_view(), name="introspect"),
]


management_urlpatterns = [
    # Application management views
    # url(r"^apps$", views.ApplicationList.as_view(), name="list"),
    path(r"^apps$", views.ApplicationRegistration.as_view(), name="register"),
    path(r"^apps/(?P<pk>[\w-]+)$", views.ApplicationDetail.as_view(), name="detail"),
    path(
        r"^apps/(?P<pk>[\w-]+)/delete$",
        views.ApplicationDelete.as_view(),
        name="delete",
    ),
    path(
        r"^apps/(?P<pk>[\w-]+)/update$",
        views.ApplicationUpdate.as_view(),
        name="update",
    ),
    # Token management views
    path(
        r"^authorized_tokens$",
        views.AuthorizedTokensListView.as_view(),
        name="authorized-token-list",
    ),
    path(
        r"^authorized_tokens/(?P<pk>[\w-]+)/delete$",
        views.AuthorizedTokenDeleteView.as_view(),
        name="authorized-token-delete",
    ),
]


urlpatterns = base_urlpatterns + management_urlpatterns
