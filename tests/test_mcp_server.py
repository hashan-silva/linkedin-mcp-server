import asyncio
import json
import unittest

from src.mcp_server import MCPServer


class _StubClient:
    def __init__(self, profile: dict, post_response: dict | None = None):
        self._profile = profile
        self._post_response = post_response or {"id": "post-1"}

    def get_profile(self) -> dict:
        return self._profile

    def create_post(self, **kwargs) -> dict:
        return self._post_response


class MCPServerTests(unittest.TestCase):
    def test_tools_call_get_profile_returns_profile_json(self) -> None:
        server = MCPServer(access_token="token")
        server.client = _StubClient({"id": "abc", "localizedFirstName": "Example"})

        response = asyncio.run(
            server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": "get_profile", "arguments": {}},
                }
            )
        )

        self.assertIsNotNone(response)
        self.assertEqual(response["id"], 1)

        content_text = response["result"]["content"][0]["text"]
        self.assertEqual(json.loads(content_text), {"id": "abc", "localizedFirstName": "Example"})

    def test_tools_call_create_post_returns_payload(self) -> None:
        server = MCPServer(access_token="token")
        server.client = _StubClient({}, {"id": "post-123"})

        response = asyncio.run(
            server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "create_post",
                        "arguments": {
                            "author": "urn:li:person:abc",
                            "commentary": "Testing",
                        },
                    },
                }
            )
        )

        self.assertIsNotNone(response)
        self.assertEqual(response["id"], 2)

        content_text = response["result"]["content"][0]["text"]
        self.assertEqual(json.loads(content_text), {"id": "post-123"})
