import os
from pathlib import Path

import requests


TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
AUTHOR_URN = os.getenv("LINKEDIN_AUTHOR_URN")

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "drafts"

RESTLI_HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "X-Restli-Protocol-Version": "2.0.0",
    "Content-Type": "application/json",
}


def _check_env():
    missing = []

    if not TOKEN:
        missing.append("LINKEDIN_ACCESS_TOKEN")

    if not AUTHOR_URN:
        missing.append("LINKEDIN_AUTHOR_URN")

    if missing:
        raise RuntimeError(
            "Missing LinkedIn configuration: "
            + ", ".join(missing)
        )

    if not AUTHOR_URN.startswith("urn:li:person:"):
        raise RuntimeError(
            "LINKEDIN_AUTHOR_URN must look like "
            "'urn:li:person:123456789'"
        )


def get_latest_draft() -> Path:
    if not DRAFTS.exists():
        raise RuntimeError("drafts/ does not exist")

    dirs = sorted(
        d for d in DRAFTS.iterdir()
        if d.is_dir()
        and d.name != "posted"
        and (d / "post.txt").exists()
    )

    if not dirs:
        raise RuntimeError("No publishable draft found")

    return dirs[-1]


def upload_image(image_path: Path) -> str:
    payload = {
        "registerUploadRequest": {
            "recipes": [
                "urn:li:digitalmediaRecipe:feedshare-image"
            ],
            "owner": AUTHOR_URN,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier":
                        "urn:li:userGeneratedContent",
                }
            ],
        }
    }

    response = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers=RESTLI_HEADERS,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    mechanism = data["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]

    upload_url = mechanism["uploadUrl"]
    asset_urn = data["value"]["asset"]

    with image_path.open("rb") as fh:
        upload_response = requests.put(
            upload_url,
            headers={
                "Authorization": f"Bearer {TOKEN}",
            },
            data=fh,
            timeout=60,
        )

    upload_response.raise_for_status()

    print("✓ LinkedIn image uploaded")
    print("  Asset:", asset_urn)

    return asset_urn


def publish_post(
    text: str,
    asset_urn: str | None = None,
) -> str:

    share_content = {
        "shareCommentary": {
            "text": text,
        },
        "shareMediaCategory":
            "IMAGE" if asset_urn else "NONE",
    }

    if asset_urn:
        share_content["media"] = [
            {
                "status": "READY",
                "media": asset_urn,
            }
        ]

    payload = {
        "author": AUTHOR_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent":
                share_content
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility":
                "PUBLIC"
        },
    }

    response = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=RESTLI_HEADERS,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    post_id = response.headers.get(
        "X-RestLi-Id",
        "unknown",
    )

    print("✓ LinkedIn post published")
    print("  Post ID:", post_id)

    return post_id


def main():
    _check_env()

    draft = get_latest_draft()

    print("Publishing:", draft.name)

    post_text = (
        draft / "post.txt"
    ).read_text().strip()

    if not post_text:
        raise RuntimeError("post.txt is empty")

    image = draft / "card.png"

    asset_urn = None

    if image.exists():
        asset_urn = upload_image(image)

    publish_post(
        text=post_text,
        asset_urn=asset_urn,
    )


if __name__ == "__main__":
    main()
