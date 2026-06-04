"""Permanently redirect the old domain (danaoj.online) to the new one (oj.koddy.online),
preserving path + query string. Registered first in MIDDLEWARE via local_settings."""
from django.http import HttpResponsePermanentRedirect

OLD_HOSTS = {"danaoj.online", "www.danaoj.online"}
NEW_BASE = "https://oj.koddy.online"


class DanaojToKoddyRedirect:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        if host in OLD_HOSTS:
            return HttpResponsePermanentRedirect(NEW_BASE + request.get_full_path())
        return self.get_response(request)
