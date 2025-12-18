import unittest

import requests

from src.linkedin_client import LinkedInClient


class _StubResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("boom")


class _StubSession:
    def __init__(self):
        self.headers = {}
        self.calls = []

    def get(self, url, params=None, **kwargs):
        self.calls.append(("GET", url, params))
        if url.endswith("/v2/userinfo"):
            return _StubResponse({"sub": "abc", "name": "Example"})
        return _StubResponse({}, status_code=404)


class LinkedInClientTests(unittest.TestCase):
    def test_get_profile_calls_userinfo_without_projection(self) -> None:
        client = LinkedInClient("token")
        client.session = _StubSession()

        profile = client.get_profile()

        self.assertEqual(profile["sub"], "abc")
        self.assertEqual(client.session.calls, [("GET", "https://api.linkedin.com/v2/userinfo", None)])
