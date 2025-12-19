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

    def post(self, url, json=None, headers=None, **kwargs):
        self.calls.append(("POST", url, json, headers or {}))
        if url.endswith("/rest/posts"):
            return _StubResponse({"id": "post-123"})
        return _StubResponse({}, status_code=404)


class LinkedInClientTests(unittest.TestCase):
    def test_get_profile_calls_userinfo_without_projection(self) -> None:
        client = LinkedInClient("token")
        client.session = _StubSession()

        profile = client.get_profile()

        self.assertEqual(profile["sub"], "abc")
        self.assertEqual(client.session.calls, [("GET", "https://api.linkedin.com/v2/userinfo", None)])

    def test_create_post_calls_posts_endpoint_with_defaults(self) -> None:
        client = LinkedInClient("token")
        client.session = _StubSession()

        response = client.create_post(
            author="urn:li:person:abc",
            commentary="Hello world",
        )

        self.assertEqual(response["id"], "post-123")
        self.assertEqual(
            client.session.calls,
            [
                (
                    "POST",
                    "https://api.linkedin.com/rest/posts",
                    {
                        "author": "urn:li:person:abc",
                        "commentary": "Hello world",
                        "visibility": "PUBLIC",
                        "distribution": {
                            "feedDistribution": "MAIN_FEED",
                            "targetEntities": [],
                            "thirdPartyDistributionChannels": [],
                        },
                        "lifecycleState": "PUBLISHED",
                        "isReshareDisabledByAuthor": False,
                    },
                    {"LinkedIn-Version": "202502"},
                )
            ],
        )
