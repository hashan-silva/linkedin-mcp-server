import asyncio
import json
import unittest

from src.mcp_server import MCPServer


class _StubClient:
    def __init__(self, profile: dict):
        self._profile = profile

    def get_profile(self) -> dict:
        return self._profile


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
