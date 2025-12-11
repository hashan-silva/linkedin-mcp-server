import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass
class ExperiencePayload:
    title: str
    company_name: str
    employment_type: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    start_year: Optional[int] = None
    start_month: Optional[int] = None
    start_day: Optional[int] = None
    end_year: Optional[int] = None
    end_month: Optional[int] = None
    end_day: Optional[int] = None
    is_current: bool = False
    position_id: Optional[str] = None


class LinkedInClient:
    def __init__(self, access_token: str, base_url: str = "https://api.linkedin.com") -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            }
        )
        self._cached_author_urn: Optional[str] = None

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _ensure_author_urn(self) -> str:
        if self._cached_author_urn:
            return self._cached_author_urn

        profile = self.get_profile()
        profile_id = profile.get("id")
        urn = profile_id if str(profile_id).startswith("urn:li:person") else f"urn:li:person:{profile_id}"
        self._cached_author_urn = urn
        return urn

    def get_profile(self) -> Dict[str, Any]:
        resp = self.session.get(
            self._url("/v2/me"),
            params=
            {
                "projection": "(id,localizedFirstName,localizedLastName,vanityName,headline,industryName,summary,locationName,profilePicture(displayImage~:playableStreams))"
            },
        )
        resp.raise_for_status()
        return resp.json()

    def update_profile(self, update: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.session.patch(self._url("/v2/me"), json=update, headers={"Content-Type": "application/merge-patch+json"})
        resp.raise_for_status()
        return resp.json()

    def upsert_experience(self, exp: ExperiencePayload) -> Dict[str, Any]:
        person_urn = self._ensure_author_urn()
        payload: Dict[str, Any] = {
            "personUrn": person_urn,
            "title": exp.title,
            "companyName": exp.company_name,
            "employmentType": exp.employment_type,
            "location": exp.location,
            "description": exp.description,
            "startDate": {"year": exp.start_year, "month": exp.start_month, "day": exp.start_day},
            "endDate": {"year": exp.end_year, "month": exp.end_month, "day": exp.end_day},
            "isCurrent": exp.is_current,
        }

        if exp.position_id:
            resp = self.session.patch(
                self._url(f"/v2/positions/{exp.position_id}"),
                json=payload,
                headers={"Content-Type": "application/merge-patch+json"},
            )
        else:
            resp = self.session.post(self._url("/v2/positions"), json=payload)

        resp.raise_for_status()
        return resp.json()

    def create_post(
        self,
        text: str,
        author_urn: Optional[str] = None,
        visibility: str = "PUBLIC",
        media_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        author = author_urn or self._ensure_author_urn()
        payload: Dict[str, Any] = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "ARTICLE" if media_url else "NONE",
                    "media": [
                        {
                            "status": "READY",
                            "originalUrl": media_url,
                        }
                    ]
                    if media_url
                    else [],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }

        resp = self.session.post(self._url("/v2/ugcPosts"), json=payload)
        resp.raise_for_status()
        return resp.json()

    def comment_on_entity(self, entity_urn: str, message: str) -> Dict[str, Any]:
        actor = self._ensure_author_urn()
        encoded = urllib.parse.quote(entity_urn, safe="")
        resp = self.session.post(
            self._url(f"/v2/socialActions/{encoded}/comments"),
            json={"actor": actor, "message": {"text": message}},
        )
        resp.raise_for_status()
        return resp.json()

    def react_to_entity(self, entity_urn: str, reaction_type: str) -> Dict[str, Any]:
        actor = self._ensure_author_urn()
        encoded = urllib.parse.quote(entity_urn, safe="")
        resp = self.session.post(
            self._url(f"/v2/socialActions/{encoded}/likes"),
            json={"actor": actor, "reactionType": reaction_type},
        )
        resp.raise_for_status()
        return resp.json()

    def send_invitation(self, profile_urn: str, message: Optional[str] = None) -> Dict[str, Any]:
        profile_id = profile_urn.split(":")[-1]
        payload = {
            "invitee": {"com.linkedin.voyager.growth.invitation.InviteeProfile": {"profileId": profile_id}},
            "message": message,
        }
        resp = self.session.post(self._url("/v2/invitations"), json=payload)
        resp.raise_for_status()
        return resp.json()

    def search(self, keywords: str, result_type: str, count: int = 10, start: int = 0, location: Optional[str] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"q": "all", "keywords": keywords, "origin": "MCP", "count": count, "start": start}
        if location:
            params["location"] = location
        if result_type:
            params["filters"] = f"resultType-{result_type}"
        resp = self.session.get(self._url("/v2/search/blended"), params=params)
        resp.raise_for_status()
        return resp.json()
