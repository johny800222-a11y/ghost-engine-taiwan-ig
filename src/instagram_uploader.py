"""
Publishes Reels to Instagram via the Instagram Graph API (Instagram Login
flow — instagram_business_content_publish scope).

Instagram's Content Publishing API does not accept direct file uploads: it
requires a publicly reachable URL for the video, which it fetches
server-side. This project hosts the source video files as assets attached
to a GitHub Release in this same repo (public repo -> release asset
download URLs are public, no auth needed), and points the API at those
URLs.

Publishing flow (two-step, per Meta's API):
  1. POST /{ig-user-id}/media  with media_type=REELS, video_url, caption
     -> creation_id
  2. Poll GET /{creation_id}?fields=status_code until FINISHED
  3. POST /{ig-user-id}/media_publish  with creation_id -> published media id

Credentials (IG_ACCESS_TOKEN, IG_BUSINESS_ACCOUNT_ID) are read from
environment variables — in GitHub Actions these come from repo secrets,
never committed to the repo.
"""
import os
import time

import requests

GRAPH_API_BASE = "https://graph.instagram.com/v21.0"

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_BUSINESS_ACCOUNT_ID = os.getenv("IG_BUSINESS_ACCOUNT_ID")


def publish_reel(video_url: str, caption: str) -> str:
    """Publish a single Reel given its public video URL and caption.

    Returns the published media id.
    """
    if not IG_ACCESS_TOKEN or not IG_BUSINESS_ACCOUNT_ID:
        raise RuntimeError(
            "IG_ACCESS_TOKEN / IG_BUSINESS_ACCOUNT_ID not set in environment "
            "(expected as GitHub Actions secrets)"
        )

    create_resp = requests.post(
        f"{GRAPH_API_BASE}/{IG_BUSINESS_ACCOUNT_ID}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=30,
    )
    if not create_resp.ok:
        print(f"media creation failed: {create_resp.status_code} {create_resp.text}")
    create_resp.raise_for_status()
    creation_id = create_resp.json()["id"]
    print(f"created media container: {creation_id}")

    # Instagram processes the video asynchronously; poll until ready.
    for _ in range(60):
        status_resp = requests.get(
            f"{GRAPH_API_BASE}/{creation_id}",
            params={"fields": "status_code", "access_token": IG_ACCESS_TOKEN},
            timeout=15,
        )
        status_resp.raise_for_status()
        status = status_resp.json().get("status_code")
        print(f"status: {status}")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError(
                f"Instagram failed to process video (creation_id={creation_id})"
            )
        time.sleep(5)
    else:
        raise TimeoutError(
            f"Instagram video processing timed out (creation_id={creation_id})"
        )

    publish_resp = requests.post(
        f"{GRAPH_API_BASE}/{IG_BUSINESS_ACCOUNT_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
        timeout=30,
    )
    publish_resp.raise_for_status()
    media_id = publish_resp.json()["id"]
    print(f"published Instagram Reel: {media_id}")
    return media_id


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("usage: python3 instagram_uploader.py <video_url> <caption>")
        sys.exit(1)
    publish_reel(sys.argv[1], sys.argv[2])
