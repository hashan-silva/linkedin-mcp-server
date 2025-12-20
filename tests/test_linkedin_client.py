from src.linkedin_client import LinkedInClient


def test_build_post_payload_preserves_full_commentary() -> None:
    client = LinkedInClient(access_token="token")
    payload = client._build_post_payload(
        author="urn:li:person:123",
        commentary="First sentence. Second sentence.",
        visibility="PUBLIC",
        distribution=None,
        lifecycle_state="PUBLISHED",
        is_reshare_disabled_by_author=False,
    )

    assert payload["commentary"]["text"] == "First sentence. Second sentence."


def test_build_post_payload_preserves_newlines() -> None:
    client = LinkedInClient(access_token="token")
    payload = client._build_post_payload(
        author="urn:li:person:123",
        commentary="First sentence.\nSecond sentence.",
        visibility="PUBLIC",
        distribution=None,
        lifecycle_state="PUBLISHED",
        is_reshare_disabled_by_author=False,
    )

    assert payload["commentary"]["text"] == "First sentence.\nSecond sentence."
