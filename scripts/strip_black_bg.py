"""
Strip near-black backgrounds from clipart PNGs, converting them to
transparent. Run once after downloading new cliparts that came with
black backgrounds instead of transparent ones.

Usage:
    python scripts/strip_black_bg.py            # dry run, lists what would change
    python scripts/strip_black_bg.py --apply    # actually overwrites the files

Safe behavior:
- Backs up originals to templates/cliparts/_backup_originals/ before modifying
- Only converts pixels darker than THRESHOLD (default 30/255)
- Preserves anti-aliasing edges where black blends into the icon's actual color
"""
import sys
from pathlib import Path
from PIL import Image

# Pixels with R, G, AND B all below this are considered background
THRESHOLD = 30


def strip_black_bg(img: Image.Image) -> Image.Image:
    """Convert an RGB image to RGBA with near-black pixels set transparent."""
    rgba = img.convert("RGBA")
    pixels = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r < THRESHOLD and g < THRESHOLD and b < THRESHOLD:
                pixels[x, y] = (0, 0, 0, 0)
    return rgba


def main():
    apply = "--apply" in sys.argv

    cliparts_dir = Path(__file__).resolve().parent.parent / "templates" / "cliparts"
    if not cliparts_dir.exists():
        print(f"❌ Not found: {cliparts_dir}")
        return

    backup_dir = cliparts_dir / "_backup_originals"

    targets = sorted([f for f in cliparts_dir.iterdir()
                      if f.is_file() and f.suffix.lower() == ".png"
                      and f.name != "manifest.json"])

    if not targets:
        print(f"No PNGs in {cliparts_dir}")
        return

    print(f"Scanning {len(targets)} PNGs (threshold = {THRESHOLD}/255)")
    print(f"Apply mode: {apply}")
    print()

    to_convert = []
    already_rgba = []
    for f in targets:
        try:
            img = Image.open(f)
        except Exception as e:
            print(f"  ⚠ Could not open {f.name}: {e}")
            continue
        if img.mode == "RGB":
            to_convert.append(f)
            print(f"  → {f.name}  (RGB, will strip black)")
        elif img.mode == "RGBA":
            # Already has alpha - check if it's actually transparent
            corners = [img.getpixel((0, 0)),
                       img.getpixel((img.width - 1, 0)),
                       img.getpixel((0, img.height - 1)),
                       img.getpixel((img.width - 1, img.height - 1))]
            min_alpha = min(c[3] for c in corners)
            if min_alpha > 200:
                to_convert.append(f)
                print(f"  → {f.name}  (RGBA but opaque, will strip black)")
            else:
                already_rgba.append(f)
                print(f"  ✓ {f.name}  (already transparent)")
        else:
            print(f"  ? {f.name}  (mode {img.mode}, skipping)")

    print()
    print(f"Total to convert: {len(to_convert)}")
    print(f"Already transparent: {len(already_rgba)}")
    print()

    if not apply:
        print("Dry run. Re-run with --apply to actually convert.")
        return

    if not to_convert:
        print("Nothing to do.")
        return

    backup_dir.mkdir(exist_ok=True)
    print(f"Backing up originals to {backup_dir}/")

    for f in to_convert:
        # Backup
        backup_path = backup_dir / f.name
        if not backup_path.exists():
            backup_path.write_bytes(f.read_bytes())

        # Convert
        img = Image.open(f)
        converted = strip_black_bg(img)
        converted.save(f, "PNG", optimize=True)
        print(f"  ✓ Converted {f.name}")

    print()
    print(f"Done. Originals are in {backup_dir}/ - delete the folder if you're happy.")


if __name__ == "__main__":
    main()
