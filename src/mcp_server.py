import argparse
import asyncio
import json
import os
import sys
import time
import urllib.parse
from typing import Any, Dict, List, Optional

from .linkedin_client import LinkedInClient
from .oauth import build_authorize_url, exchange_code_for_token, start_local_redirect_server


class MCPServer:
    def __init__(self, access_token: str, base_url: str = "https://api.linkedin.com") -> None:
        self.client = LinkedInClient(access_token=access_token, base_url=base_url)

    async def run(self) -> None:
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())

        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                message = json.loads(line.decode())
            except Exception:
                continue

            response = await self.handle_message(message)
            if response is not None:
                writer.write((json.dumps(response) + "\n").encode())
                await writer.drain()

    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = message.get("method")
        request_id = message.get("id")

        if method == "initialize":
            return self._response(
                request_id,
                {
                    "protocolVersion": "0.1",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "linkedin-mcp-server", "version": "0.1.0"},
                },
            )

        if method in {"list_tools", "tools/list"}:
            return self._response(request_id, {"tools": self.tools()})

        if method in {"call_tool", "tools/call"}:
            params = message.get("params", {})
            name = params.get("name")
            args = params.get("arguments") or {}
            try:
                result = await self.invoke_tool(name, args)
                return self._response(request_id, {"content": [{"type": "text", "text": json.dumps(result)}]})
            except Exception as exc:  # pragma: no cover - surfaced to client
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32000, "message": str(exc)},
                }

        return None

    def _response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_profile",
                "description": "Fetch current profile info (id, names, headline, summary, location, picture).",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    async def invoke_tool(self, name: str, args: Dict[str, Any]) -> Any:
        if name == "get_profile":
            return self.client.get_profile()
        raise ValueError(f"Unknown tool: {name}")


def env_or_raise(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="LinkedIn MCP server")
    parser.add_argument("--auth", action="store_true", help="Run OAuth flow to fetch access token before starting server")
    args = parser.parse_args()

    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    base_url = os.getenv("LINKEDIN_BASE_URL", "https://api.linkedin.com")

    if args.auth and not token:
        client_id = env_or_raise("LINKEDIN_CLIENT_ID")
        client_secret = env_or_raise("LINKEDIN_CLIENT_SECRET")
        redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "http://127.0.0.1:8765/callback")
        scope = os.getenv("LINKEDIN_SCOPE", "r_liteprofile w_member_social")

        parsed_redirect = urllib.parse.urlparse(redirect_uri)
        host = parsed_redirect.hostname or "127.0.0.1"
        port = parsed_redirect.port or (443 if parsed_redirect.scheme == "https" else 80)
        server_http, thread, code_container = start_local_redirect_server(host, port)

        auth_url = build_authorize_url(client_id, redirect_uri, scope)
        print("Open this URL in a browser to authorize:")
        print(auth_url, flush=True)

        print("Waiting for redirect with code...")
        while code_container.get("code") is None:
            time.sleep(0.2)

        server_http.shutdown()
        code = code_container.get("code")
        if not code:
            raise RuntimeError("Failed to capture authorization code")

        token_result = exchange_code_for_token(client_id, client_secret, redirect_uri, code)
        token = token_result.access_token
        print("Access token acquired; starting MCP server...", flush=True)

    if not token:
        token = env_or_raise("LINKEDIN_ACCESS_TOKEN")

    mcp = MCPServer(access_token=token, base_url=base_url)
    asyncio.run(mcp.run())


if __name__ == "__main__":
    main()
