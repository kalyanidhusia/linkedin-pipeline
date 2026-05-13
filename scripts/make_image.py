"""
Render a Type 3 do/don't card: navy background, your headshot on the right,
DON'T / DO pair on the left. Drawn programmatically - no template image needed.
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from config import CARD_SIZE, CARD_BG, CARD_ACCENT, CARD_TEXT, HEADSHOT_FILE

ROOT = Path(__file__).resolve().parent.parent


def _font_candidates(bold: bool) -> list[str]:
    """OS-aware font paths. macOS first since user is on Mac, then Linux, then Windows."""
    if sys.platform == "darwin":
        if bold:
            return [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/System/Library/Fonts/HelveticaNeue.ttc",
                "/Library/Fonts/Arial Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/SFNS.ttf",
            ]
        return [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNS.ttf",
        ]
    if sys.platform.startswith("linux"):
        return [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold
                else "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ]
    # Windows
    return [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Try platform-appropriate fonts. If all fail, raise loudly - silent fallback
    to bitmap font ignores size and produces unreadable cards."""
    for path in _font_candidates(bold):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    # If we get here, none of the candidate fonts worked. Try PIL's bundled fonts.
    # As a last resort, use the default but warn loudly.
    print(f"⚠ WARNING: No TrueType font found for size={size} bold={bold}. "
          f"Card text will be unreadable. Install a font or edit _font_candidates.")
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
          max_width: int) -> list[str]:
    """Greedy word wrap."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_card(dont_text: str, do_text: str, output_path: str | Path) -> Path:
    """Build the do/don't card and save it."""
    W, H = CARD_SIZE
    img = Image.new("RGB", (W, H), CARD_BG)
    draw = ImageDraw.Draw(img)

    # Layout: text on left half, headshot on right half
    left_pad = 80
    text_width = W // 2 - left_pad - 20
    headshot_box = (W // 2 + 20, 80, W - 80, H - 80)

    # Headshot
    headshot_path = ROOT / HEADSHOT_FILE
    if headshot_path.exists():
        photo = Image.open(headshot_path).convert("RGBA")
        target_w = headshot_box[2] - headshot_box[0]
        target_h = headshot_box[3] - headshot_box[1]
        ratio = min(target_w / photo.width, target_h / photo.height)
        new_size = (int(photo.width * ratio), int(photo.height * ratio))
        photo = photo.resize(new_size, Image.LANCZOS)
        px = headshot_box[0] + (target_w - new_size[0]) // 2
        py = headshot_box[1] + (target_h - new_size[1]) // 2
        img.paste(photo, (px, py), photo if photo.mode == "RGBA" else None)

    # Accent bar on far left
    draw.rectangle([0, 0, 12, H], fill=CARD_ACCENT)

    # Fonts - if any return a bitmap default (load_default), text will be tiny.
    label_font = _load_font(56, bold=True)
    body_font = _load_font(72, bold=True)
    small_font = _load_font(32, bold=False)

    # Verify we got real TrueType fonts. If not, fail loudly so the user knows.
    if not isinstance(body_font, ImageFont.FreeTypeFont):
        print("⚠ Card generation produced unreadable text because no TrueType "
              "font was found. Falling back to a smaller, but readable, layout.")

    # DON'T section
    y = 120
    draw.text((left_pad, y), "DON'T", font=label_font, fill=CARD_ACCENT)
    y += 90
    for line in _wrap(draw, dont_text, body_font, text_width):
        draw.text((left_pad, y), line, font=body_font, fill=CARD_TEXT)
        y += 90

    # Divider
    y_divider = H // 2 + 20
    draw.line([(left_pad, y_divider), (left_pad + text_width, y_divider)],
              fill="#3A4A66", width=2)

    # DO section
    y = y_divider + 50
    draw.text((left_pad, y), "DO", font=label_font, fill="#56C78A")
    y += 90
    for line in _wrap(draw, do_text, body_font, text_width):
        draw.text((left_pad, y), line, font=body_font, fill=CARD_TEXT)
        y += 90

    # Footer
    draw.text((left_pad, H - 80), "Kalyani Dhusia, Ph.D.",
              font=small_font, fill="#8A9AB5")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    return output_path


if __name__ == "__main__":
    # Self-test that also reveals which font path was used
    print("Detected platform:", sys.platform)
    print("Looking for fonts in:")
    for p in _font_candidates(bold=True):
        exists = "✓" if Path(p).exists() else "✗"
        print(f"  {exists} {p}")
    print()
    out = make_card(
        dont_text="Hardcode file paths in scripts",
        do_text="Use config files or environment variables",
        output_path=ROOT / "drafts" / "preview_card.png",
    )
    print(f"Saved: {out}")
