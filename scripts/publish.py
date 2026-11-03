import os
import requests
from pathlib import Path

LI_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN")
AUTHOR_URN = os.environ.get("LINKEDIN_AUTHOR_URN")
ROOT = Path(__file__).resolve().parent.parent

def get_latest_draft():
    drafts_dir = ROOT / "drafts"
    if not drafts_dir.exists():
        return None
    dirs = sorted([d for d in drafts_dir.iterdir() if d.is_dir() and d.name != "posted"], reverse=True)
    return dirs[0] if dirs else None

def post_to_linkedin(draft_dir):
    post_text = (draft_dir / "post.txt").read_text()
    img_path = draft_dir / "card.png"
    
    headers = {"Authorization": f"Bearer {LI_TOKEN}", "Content-Type": "application/json"}
    asset_urn = None

    if img_path.exists():
        register_payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": AUTHOR_URN,
                "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
            }
        }
        upload_res = requests.post("https://api.linkedin.com/v2/assets?action=registerUpload", headers=headers, json=register_payload).json()
        upload_url = upload_res['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset_urn = upload_res['value']['asset']
        
        with open(img_path, 'rb') as f:
            requests.put(upload_url, headers={"Authorization": f"Bearer {LI_TOKEN}"}, data=f)

    post_payload = {
        "author": AUTHOR_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_text},
                "shareMediaCategory": "IMAGE" if asset_urn else "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    
    if asset_urn:
        post_payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{"status": "READY", "media": asset_urn}]
    
    res = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=post_payload)
    res.raise_for_status()

if __name__ == "__main__":
    latest = get_latest_draft()
    if latest:
        post_to_linkedin(latest)
        # Optional: move folder to 'posted' directory here
