"""
Smart background removal for the headshot. Strategy:

1. If templates/headshot_cutout.png exists, use it directly. Zero processing.
2. Otherwise, run rembg on templates/headshot.png to produce headshot_cutout.png,
   then use that. Subsequent runs hit step 1.
3. If rembg isn't installed, fall back to flood-fill (the previous method).

This means cutout cost is paid once. Every weekly card after the first uses
the cached transparent PNG and runs in well under a second.
"""

from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"

HEADSHOT_ORIGINAL = TEMPLATES / "headshot.png"
HEADSHOT_CUTOUT = TEMPLATES / "headshot_cutout.png"


def _rembg_cutout(src: Path, dst: Path) -> bool:
    """Run rembg to produce a transparent-background cutout. Returns True on success."""
    try:
        from rembg import remove
    except ImportError:
        return False

    print(f"  → Running rembg on {src.name} (first time only, ~10s)...")
    with open(src, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    with open(dst, "wb") as f:
        f.write(output_bytes)
    print(f"  → Cached cutout to {dst.name}. Future runs will be instant.")
    return True


def _flood_fill_cutout(src: Path, dst: Path, threshold: int = 50) -> None:
    """Fallback: flood-fill from corners. Less accurate but no dependencies."""
    print(f"  → rembg not installed; using flood-fill cutout (lower quality).")
    print(f"  → For best quality: pip install rembg onnxruntime")
    photo = Image.open(src).convert("RGBA")
    w, h = photo.size
    pixels = photo.load()

    is_bg = [[False] * h for _ in range(w)]
    visited = [[False] * h for _ in range(w)]

    def brightness(x, y):
        r, g, b, _ = pixels[x, y]
        return (r + g + b) / 3

    seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    stack = []
    for sx, sy in seeds:
        if brightness(sx, sy) < threshold:
            stack.append((sx, sy))

    while stack:
        x, y = stack.pop()
        if x < 0 or x >= w or y < 0 or y >= h:
            continue
        if visited[x][y]:
            continue
        visited[x][y] = True
        if brightness(x, y) >= threshold:
            continue
        is_bg[x][y] = True
        stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

    for y in range(h):
        for x in range(w):
            if is_bg[x][y]:
                r, g, b, _ = pixels[x, y]
                pixels[x, y] = (r, g, b, 0)

    r_ch, g_ch, b_ch, a_ch = photo.split()
    a_ch = a_ch.filter(ImageFilter.GaussianBlur(radius=1.5))
    photo = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_ch))
    photo.save(dst, "PNG")


def get_headshot() -> Image.Image:
    """Return the cutout headshot, generating it if needed."""
    if HEADSHOT_CUTOUT.exists():
        return Image.open(HEADSHOT_CUTOUT).convert("RGBA")

    if not HEADSHOT_ORIGINAL.exists():
        raise FileNotFoundError(
            f"No headshot found. Put your photo at {HEADSHOT_ORIGINAL}"
        )

    print(f"⚙ No cached cutout found. Generating one from {HEADSHOT_ORIGINAL.name}...")
    if not _rembg_cutout(HEADSHOT_ORIGINAL, HEADSHOT_CUTOUT):
        _flood_fill_cutout(HEADSHOT_ORIGINAL, HEADSHOT_CUTOUT)
    return Image.open(HEADSHOT_CUTOUT).convert("RGBA")


if __name__ == "__main__":
    img = get_headshot()
    preview = ROOT / "drafts" / "cutout_preview.png"
    preview.parent.mkdir(exist_ok=True)
    img.save(preview)
    print(f"Saved cutout preview to: {preview}")
    print(f"Size: {img.size}, mode: {img.mode}")
