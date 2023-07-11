import io
import json

import requests as requests
from PIL import ImageFile
from django.http import HttpResponse, HttpResponseServerError
from requests.exceptions import ChunkedEncodingError

from freefeeds.client import Client


def _generic_feed_data(request, client_handler):
    client = Client.from_request(request)
    data = client_handler(client)
    return HttpResponse(json.dumps(data), content_type="application/json")


def verify_credentials(request):
    return _generic_feed_data(request, lambda c: c.get_me().to_md_json())


def timelines_account(request, uid):
    return _generic_feed_data(
        request, lambda c: [p.to_md_json() for p in c.get_user_timeline(uid)]
    )


def account(request, uid):
    return _generic_feed_data(request, lambda c: c.get_user(uid).to_md_json())


def timelines_public(request):
    return _generic_feed_data(request, lambda c: [])


def timelines_home(request):
    params = {}
    if request.GET.get("limit"):
        params["limit"] = int(request.GET.get("limit"))
    if request.GET.get("max_id"):
        params["max_id"] = int(request.GET.get("max_id"))
    if request.GET.get("since_id"):
        params["since_id"] = int(request.GET.get("since_id"))
    return _generic_feed_data(
        request, lambda c: [p.to_md_json() for p in c.get_home(**params)]
    )


def status_detail(request, md_id):
    return _generic_feed_data(request, lambda c: c.get_post(md_id)[0].to_md_json())


def status_context(request, md_id):
    return _generic_feed_data(
        request,
        lambda c: {
            "ancestors": [],
            "descendants": [p.to_md_json() for p in c.get_post(md_id)[1:]],
        },
    )


def status_post(request):
    return _generic_feed_data(
        request, lambda c: c.new_post_or_comment(request.POST).to_md_json()
    )


def status_like(request, md_id):
    return _generic_feed_data(request, lambda c: c.post_like(md_id).to_md_json())


def status_unlike(request, md_id):
    return _generic_feed_data(request, lambda c: c.post_unlike(md_id).to_md_json())


def upload_attachment(request):
    return _generic_feed_data(
        request, lambda c: c.new_attachment(request.FILES["file"]).to_md_json()
    )


def filters(request):
    return _generic_feed_data(request, lambda c: [])


def notifications(request):
    return _generic_feed_data(request, lambda c: c.get_notifications())


def instance_info(request):
    data = {"uri": "http://feedodon.rkd.pw/", "title": "feedik bridge", "version": "1"}
    return HttpResponse(json.dumps(data), content_type="application/json")


def apps(request):
    # TODO save app and retrieve the data
    data = {
        "id": 0,
        "name": "Tusky",
        "website": "",
        "redirect_uri": [],
        "client_id": "client_id",
        "client_secret": "client_secret",
    }
    return HttpResponse(json.dumps(data), content_type="application/json")


def nodeinfo_v1(request):
    data = {
        "links": [
            {
                "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
                "href": "https://feedodon.rkd.pw/nodeinfo/2.0",
            }
        ]
    }
    return HttpResponse(json.dumps(data), content_type="application/json")


def nodeinfo_v2(request):
    data = {
        "version": "2.0",
        "software": {"name": "feedodon", "version": "0.1"},
        "protocols": ["activitypub"],
        "usage": {
            "users": {"total": 1, "activeMonth": 1, "activeHalfyear": 1},
            "localPosts": 100500,
        },
        "openRegistrations": False,
    }
    return HttpResponse(json.dumps(data), content_type="application/json")


def direct_messages(request):
    return HttpResponse(json.dumps([]), content_type="application/json")


def saved_searches(request):
    return HttpResponse(json.dumps([]), content_type="application/json")


def media_redirect(request, path):
    from PIL import Image
    requests.models.CONTENT_CHUNK_SIZE = 1 * 1024 * 1024

    url = "https://mokum.place/" + path.strip("/")
    print(url)

    result = HttpResponseServerError()

    with io.BytesIO() as handle:
        response = requests.get(url, stream=True)

        if response.ok:
            try:
                for block in response.iter_content(1024):
                    if not block:
                        break
                    handle.write(block)
            except ChunkedEncodingError as e:
                pass

            status_code = response.status_code
            handle.seek(0)
            ImageFile.LOAD_TRUNCATED_IMAGES = True

            img = Image.open(handle)

            result = HttpResponse(status=status_code, content_type="image/png")
            img.save(result, format="png")
    return result

