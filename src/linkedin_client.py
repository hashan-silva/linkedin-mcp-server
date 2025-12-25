from pathlib import Path
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
        resp = self.session.get(
            self._url("/rest/identityMe"),
            headers={"LinkedIn-Version": "202510.03"},
        )
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

    def get_verification_report(self, linkedin_version: str = "202510") -> Dict[str, Any]:
        resp = self.session.get(
            self._url("/rest/verificationReport"),
            headers={"LinkedIn-Version": linkedin_version},
        )
        self._raise_for_status(resp)
        return resp.json()

    def get_userinfo(self, linkedin_version: str = "202502") -> Dict[str, Any]:
        resp = self.session.get(
            self._url("/v2/userinfo"),
            headers={"LinkedIn-Version": linkedin_version},
        )
        self._raise_for_status(resp)
        return resp.json()

    def create_reshare(
        self,
        author: str,
        parent: str,
        commentary: str = "",
        visibility: str = "PUBLIC",
        distribution: Optional[Dict[str, Any]] = None,
        lifecycle_state: str = "PUBLISHED",
        is_reshare_disabled_by_author: bool = False,
        linkedin_version: str = "202401",
    ) -> Dict[str, Any]:
        payload = self._build_reshare_payload(
            author=author,
            parent=parent,
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

    def initialize_image_upload(
        self, owner: str, linkedin_version: str = "202401"
    ) -> Dict[str, Any]:
        owner_value = owner.strip() if owner else ""
        if not owner_value:
            raise ValueError("owner is required")

        resp = self.session.post(
            self._url("/rest/images?action=initializeUpload"),
            json={"initializeUploadRequest": {"owner": owner_value}},
            headers={"LinkedIn-Version": linkedin_version},
        )
        self._raise_for_status(resp)
        return resp.json()

    def upload_image_binary(self, upload_url: str, file_path: str) -> Dict[str, Any]:
        url_value = upload_url.strip() if upload_url else ""
        if not url_value:
            raise ValueError("upload_url is required")
        path = Path(file_path)
        if not path.is_file():
            raise ValueError(f"file_path not found: {file_path}")

        with path.open("rb") as handle:
            resp = requests.put(
                url_value,
                data=handle,
                headers={"Content-Type": "application/octet-stream"},
            )
        self._raise_for_status(resp)
        if resp.text:
            try:
                return resp.json()
            except ValueError:
                return {"status": resp.status_code, "body": resp.text}
        return {"status": resp.status_code}

    def create_image_post(
        self,
        author: str,
        image_urn: str,
        commentary: str,
        alt_text: str = "",
        visibility: str = "PUBLIC",
        lifecycle_state: str = "PUBLISHED",
        linkedin_version: str = "202401",
    ) -> Dict[str, Any]:
        payload = self._build_image_post_payload(
            author=author,
            image_urn=image_urn,
            commentary=commentary,
            alt_text=alt_text,
            visibility=visibility,
            lifecycle_state=lifecycle_state,
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

    def create_multi_image_post(
        self,
        author: str,
        images: list[Dict[str, str]],
        commentary: str,
        visibility: str = "PUBLIC",
        distribution: Optional[Dict[str, Any]] = None,
        lifecycle_state: str = "PUBLISHED",
        is_reshare_disabled_by_author: bool = False,
        linkedin_version: str = "202511",
    ) -> Dict[str, Any]:
        payload = self._build_multi_image_post_payload(
            author=author,
            images=images,
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

    def _build_reshare_payload(
        self,
        author: str,
        parent: str,
        commentary: str,
        visibility: str,
        distribution: Optional[Dict[str, Any]],
        lifecycle_state: str,
        is_reshare_disabled_by_author: bool,
    ) -> Dict[str, Any]:
        author_value = author.strip() if author else ""
        parent_value = parent.strip() if parent else ""
        if not author_value:
            raise ValueError("author is required")
        if not parent_value:
            raise ValueError("parent is required")

        payload: Dict[str, Any] = {
            "author": author_value,
            "visibility": visibility,
            "distribution": distribution
            or {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": lifecycle_state,
            "isReshareDisabledByAuthor": is_reshare_disabled_by_author,
            "reshareContext": {"parent": parent_value},
        }
        commentary_value = commentary.strip() if commentary else ""
        if commentary_value:
            payload["commentary"] = commentary_value
        return payload

    def _build_image_post_payload(
        self,
        author: str,
        image_urn: str,
        commentary: str,
        alt_text: str,
        visibility: str,
        lifecycle_state: str,
    ) -> Dict[str, Any]:
        author_value = author.strip() if author else ""
        image_value = image_urn.strip() if image_urn else ""
        commentary_value = commentary.strip() if commentary else ""
        if not author_value:
            raise ValueError("author is required")
        if not image_value:
            raise ValueError("image_urn is required")
        if not commentary_value:
            raise ValueError("commentary is required")

        media: Dict[str, Any] = {"id": image_value}
        alt_value = alt_text.strip() if alt_text else ""
        if alt_value:
            media["altText"] = alt_value

        return {
            "author": author_value,
            "commentary": commentary_value,
            "visibility": visibility,
            "lifecycleState": lifecycle_state,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {"media": media},
        }

    def _build_multi_image_post_payload(
        self,
        author: str,
        images: list[Dict[str, str]],
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
        if not images:
            raise ValueError("images is required")

        image_items: list[Dict[str, str]] = []
        for image in images:
            image_id = (image.get("id") or "").strip()
            if not image_id:
                raise ValueError("image id is required")
            item: Dict[str, str] = {"id": image_id}
            alt_text = (image.get("altText") or "").strip()
            if alt_text:
                item["altText"] = alt_text
            image_items.append(item)

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
            "content": {"multiImage": {"images": image_items}},
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
