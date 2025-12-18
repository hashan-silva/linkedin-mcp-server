from typing import Any, Dict

import requests
from requests import Response


class LinkedInClient:
    def __init__(self, access_token: str, base_url: str = "https://api.linkedin.com") -> None:
        if not access_token or not access_token.strip():
            raise RuntimeError(
                "LinkedIn access token is missing. Set LINKEDIN_ACCESS_TOKEN or run `python -m src.mcp_server --auth`."
            )

        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            }
        )

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get_profile(self) -> Dict[str, Any]:
        resp = self.session.get(self._url("/v2/userinfo"))
        self._raise_for_status(resp)
        return resp.json()

    def _raise_for_status(self, resp: Response) -> None:
        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            if resp.status_code in {401, 403}:
                raise RuntimeError(
                    "LinkedIn rejected the request "
                    f"(status {resp.status_code}). Ensure LINKEDIN_ACCESS_TOKEN is valid and has the required scopes, "
                    "or re-run `python -m src.mcp_server --auth` to refresh it."
                ) from exc
            raise
