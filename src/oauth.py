import http.server
import threading
import urllib.parse
from dataclasses import dataclass
from typing import Dict, Optional

import requests


@dataclass
class TokenResult:
    access_token: str
    expires_in: int
    refresh_token: Optional[str] = None


def build_authorize_url(client_id: str, redirect_uri: str, scope: str, state: str = "mcp_state") -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
    }
    return "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode(params)


def exchange_code_for_token(client_id: str, client_secret: str, redirect_uri: str, code: str) -> TokenResult:
    resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    resp.raise_for_status()
    data: Dict[str, str] = resp.json()
    return TokenResult(
        access_token=data.get("access_token", ""),
        expires_in=int(data.get("expires_in", 0)),
        refresh_token=data.get("refresh_token"),
    )


def start_local_redirect_server(host: str, port: int):
    """Start a minimal HTTP server to capture the OAuth code. Returns (server, thread, future_code)."""
    code_container: Dict[str, Optional[str]] = {"code": None}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # type: ignore
            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)
            if "code" in query:
                code_container["code"] = query["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body>You may close this window.</body></html>")
            else:
                self.send_response(400)
                self.end_headers()

        def log_message(self, format: str, *args) -> None:  # pragma: no cover - silence
            return

    httpd = http.server.HTTPServer((host, port), Handler)

    def serve():
        httpd.serve_forever()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return httpd, thread, code_container
