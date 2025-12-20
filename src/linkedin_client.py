from typing import Any, Dict, Optional

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

    def create_post(
        self,
        author: str,
        commentary: str,
        visibility: str = "PUBLIC",
        distribution: Optional[Dict[str, Any]] = None,
        lifecycle_state: str = "PUBLISHED",
        is_reshare_disabled_by_author: bool = False,
        linkedin_version: str = "202502",
    ) -> Dict[str, Any]:
        payload = self._build_post_payload(
            author=author,
            commentary=commentary,
            visibility=visibility,
            distribution=distribution,
            lifecycle_state=lifecycle_state,
            is_reshare_disabled_by_author=is_reshare_disabled_by_author,
        )

        resp = self.session.post(
            self._url("/rest/posts"),
            json=payload,
            headers={"LinkedIn-Version": linkedin_version},
        )
        self._raise_for_status(resp)
        try:
            return resp.json()
        except ValueError:
            return {"status": resp.status_code}

    def create_article_post(
        self,
        author: str,
        commentary: str,
        article_source: str,
        article_title: str,
        article_description: str,
        visibility: str = "PUBLIC",
        lifecycle_state: str = "PUBLISHED",
        distribution: Optional[Dict[str, Any]] = None,
        linkedin_version: str = "202502",
    ) -> Dict[str, Any]:
        payload = self._build_article_post_payload(
            author=author,
            commentary=commentary,
            article_source=article_source,
            article_title=article_title,
            article_description=article_description,
            visibility=visibility,
            lifecycle_state=lifecycle_state,
            distribution=distribution,
        )

        resp = self.session.post(
            self._url("/rest/posts"),
            json=payload,
            headers={"LinkedIn-Version": linkedin_version},
        )
        self._raise_for_status(resp)
        try:
            return resp.json()
        except ValueError:
            return {"status": resp.status_code}

    def _build_post_payload(
        self,
        author: str,
        commentary: str,
        visibility: str,
        distribution: Optional[Dict[str, Any]],
        lifecycle_state: str,
        is_reshare_disabled_by_author: bool,
    ) -> Dict[str, Any]:
        author_value = author.strip() if author else ""
        commentary_value = commentary.strip() if commentary else ""
        if not author_value:
            raise ValueError("author is required")
        if not commentary_value:
            raise ValueError("commentary is required")

        return {
            "author": author_value,
            "commentary": commentary_value,
            "visibility": visibility,
            "distribution": distribution
            or {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": lifecycle_state,
            "isReshareDisabledByAuthor": is_reshare_disabled_by_author,
        }

    def _build_article_post_payload(
        self,
        author: str,
        commentary: str,
        article_source: str,
        article_title: str,
        article_description: str,
        visibility: str,
        lifecycle_state: str,
        distribution: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        author_value = author.strip() if author else ""
        commentary_value = commentary.strip() if commentary else ""
        source_value = article_source.strip() if article_source else ""
        title_value = article_title.strip() if article_title else ""
        description_value = article_description.strip() if article_description else ""

        if not author_value:
            raise ValueError("author is required")
        if not commentary_value:
            raise ValueError("commentary is required")
        if not source_value:
            raise ValueError("article_source is required")
        if not title_value:
            raise ValueError("article_title is required")
        if not description_value:
            raise ValueError("article_description is required")

        return {
            "author": author_value,
            "commentary": commentary_value,
            "visibility": visibility,
            "lifecycleState": lifecycle_state,
            "content": {
                "article": {
                    "source": source_value,
                    "title": title_value,
                    "description": description_value,
                }
            },
            "distribution": distribution or {"feedDistribution": "MAIN_FEED"},
        }

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
            details = ""
            if resp.text:
                snippet = resp.text.strip().replace("\n", " ")
                details = f" Response: {snippet[:500]}"
            raise RuntimeError(
                f"LinkedIn request failed (status {resp.status_code}).{details}"
            ) from exc
