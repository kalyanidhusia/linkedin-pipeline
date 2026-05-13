"""
One-command posting workflow for the latest draft.

Usage:
  python scripts/post_now.py                # newest draft, copy + open Finder + open LinkedIn
  python scripts/post_now.py --buffer       # open Buffer instead of LinkedIn
  python scripts/post_now.py --pick         # list drafts and let me pick one
  python scripts/post_now.py --archive      # mark current draft as posted (move to drafts/posted/)

The script copies post.txt to your clipboard so you can paste directly.
For Type 3 posts, also opens the folder in Finder so you can drag card.png to the LinkedIn upload.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "drafts"
POSTED = DRAFTS / "posted"

LINKEDIN_URL = "https://www.linkedin.com/feed/?shareActive=true"
BUFFER_URL = "https://publish.buffer.com/"


def _list_drafts() -> list[Path]:
    """Return pending draft folders, newest first."""
    if not DRAFTS.exists():
        return []
    return sorted(
        [d for d in DRAFTS.iterdir()
         if d.is_dir() and d.name != "posted" and (d / "post.txt").exists()],
        reverse=True,
    )


def _copy_to_clipboard(text: str) -> bool:
    """Copy to clipboard. Cross-platform: pbcopy (Mac), xclip/wl-copy (Linux), clip (Windows)."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text, text=True, check=True)
            return True
        if sys.platform.startswith("linux"):
            if shutil.which("wl-copy"):
                subprocess.run(["wl-copy"], input=text, text=True, check=True)
                return True
            if shutil.which("xclip"):
                subprocess.run(["xclip", "-selection", "clipboard"],
                               input=text, text=True, check=True)
                return True
            return False
        if sys.platform == "win32":
            subprocess.run(["clip"], input=text, text=True, check=True, shell=True)
            return True
    except Exception as e:
        print(f"  Clipboard copy failed: {e}")
    return False


def _open(target: str) -> None:
    """Open a folder or URL in the default app."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", target], check=False)
        elif sys.platform.startswith("linux"):
            subprocess.run(["xdg-open", target], check=False)
        elif sys.platform == "win32":
            subprocess.run(["start", "", target], shell=True, check=False)
    except Exception as e:
        print(f"  Could not open {target}: {e}")


def show_and_copy(folder: Path, target: str = "linkedin") -> None:
    post_file = folder / "post.txt"
    card_file = folder / "card.png"
    meta_file = folder / "meta.json"

    if not post_file.exists():
        print(f"✗ No post.txt in {folder}")
        return

    post_text = post_file.read_text()
    meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}

    print(f"━━━ DRAFT: {folder.name} ━━━")
    print(f"Type: {meta.get('type', 'unknown')}")
    if meta.get("source_links"):
        print(f"Source links to add as comment: {len(meta['source_links'])}")
    print()
    print("──── POST TEXT ────")
    print(post_text)
    print("──────────────────")
    print()

    # Copy text to clipboard
    if _copy_to_clipboard(post_text):
        print("✓ Post text copied to clipboard")
    else:
        print("⚠ Clipboard copy not available - select the text above manually")

    # Open folder so user can grab the card.png
    if card_file.exists():
        print(f"✓ Card image: {card_file}")
        _open(str(folder))
        print("  Folder opened in Finder - drag card.png to the LinkedIn upload")

    # Open the posting destination
    if target == "buffer":
        print(f"→ Opening Buffer...")
        _open(BUFFER_URL)
    elif target == "linkedin":
        print(f"→ Opening LinkedIn compose...")
        _open(LINKEDIN_URL)
    elif target == "none":
        pass

    # Reminder for source link
    if meta.get("source_links"):
        print()
        print("📌 Reminder: post the source link as the FIRST COMMENT, not in the body.")
        print(f"   Top candidate: {meta['source_links'][0]}")


def archive_latest() -> None:
    drafts = _list_drafts()
    if not drafts:
        print("No drafts to archive.")
        return
    latest = drafts[0]
    POSTED.mkdir(exist_ok=True)
    target = POSTED / latest.name
    if target.exists():
        print(f"Already archived: {target}")
        return
    shutil.move(str(latest), str(target))
    print(f"✓ Archived: {latest.name} -> drafts/posted/")


def pick_draft() -> Path | None:
    drafts = _list_drafts()
    if not drafts:
        print("No pending drafts. Run generate_post.py first.")
        return None
    print("Pending drafts:")
    for i, d in enumerate(drafts):
        meta = {}
        if (d / "meta.json").exists():
            meta = json.loads((d / "meta.json").read_text())
        print(f"  [{i}] {d.name}  ({meta.get('type', '?')})")
    print()
    try:
        choice = int(input("Pick a draft number: ").strip())
        return drafts[choice]
    except (ValueError, IndexError, KeyboardInterrupt):
        print("Cancelled.")
        return None


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--buffer", action="store_true", help="open Buffer instead of LinkedIn")
    p.add_argument("--pick", action="store_true", help="choose from list of drafts")
    p.add_argument("--archive", action="store_true", help="archive newest draft to drafts/posted/")
    p.add_argument("--no-open", action="store_true", help="don't open browser")
    args = p.parse_args()

    if args.archive:
        archive_latest()
        return

    if args.pick:
        folder = pick_draft()
        if not folder:
            return
    else:
        drafts = _list_drafts()
        if not drafts:
            print("No pending drafts. Run generate_post.py first.")
            return
        folder = drafts[0]

    target = "none" if args.no_open else ("buffer" if args.buffer else "linkedin")
    show_and_copy(folder, target=target)


if __name__ == "__main__":
    main()
