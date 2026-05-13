"""
Render a Type 3 do/don't card: navy background, your headshot on the right,
a big DON'T / DO pair on the left. No template image needed - it's all drawn.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from config import CARD_SIZE, CARD_BG, CARD_ACCENT, CARD_TEXT, HEADSHOT_FILE

ROOT = Path(__file__).resolve().parent.parent


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Try DejaVu (always present on Ubuntu / GitHub Actions runners)."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
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

    # ── Layout: text on left half, headshot on right half ──
    left_pad = 80
    text_width = W // 2 - left_pad - 20
    headshot_box = (W // 2 + 20, 80, W - 80, H - 80)

    # ── Headshot ──
    headshot_path = ROOT / HEADSHOT_FILE
    if headshot_path.exists():
        photo = Image.open(headshot_path).convert("RGBA")
        target_w = headshot_box[2] - headshot_box[0]
        target_h = headshot_box[3] - headshot_box[1]
        ratio = min(target_w / photo.width, target_h / photo.height)
        new_size = (int(photo.width * ratio), int(photo.height * ratio))
        photo = photo.resize(new_size, Image.LANCZOS)
        # Center inside the box
        px = headshot_box[0] + (target_w - new_size[0]) // 2
        py = headshot_box[1] + (target_h - new_size[1]) // 2
        img.paste(photo, (px, py), photo if photo.mode == "RGBA" else None)

    # ── Accent bar on far left ──
    draw.rectangle([0, 0, 12, H], fill=CARD_ACCENT)

    # ── DON'T section (top half of left column) ──
    label_font = _load_font(48, bold=True)
    body_font = _load_font(64, bold=True)
    small_font = _load_font(28, bold=False)

    y = 120
    draw.text((left_pad, y), "DON'T", font=label_font, fill=CARD_ACCENT)
    y += 80
    for line in _wrap(draw, dont_text, body_font, text_width):
        draw.text((left_pad, y), line, font=body_font, fill=CARD_TEXT)
        y += 80

    # ── Divider ──
    y_divider = H // 2 + 20
    draw.line([(left_pad, y_divider), (left_pad + text_width, y_divider)],
              fill="#3A4A66", width=2)

    # ── DO section (bottom half) ──
    y = y_divider + 40
    draw.text((left_pad, y), "DO", font=label_font, fill="#56C78A")  # Green
    y += 80
    for line in _wrap(draw, do_text, body_font, text_width):
        draw.text((left_pad, y), line, font=body_font, fill=CARD_TEXT)
        y += 80

    # ── Footer / signature ──
    draw.text((left_pad, H - 80), "Kalyani Dhusia, Ph.D.",
              font=small_font, fill="#8A9AB5")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    return output_path


if __name__ == "__main__":
    out = make_card(
        dont_text="Hardcode file paths in your scripts.",
        do_text="Use a config file or environment variables.",
        output_path=ROOT / "drafts" / "preview_card.png",
    )
    print(f"Saved: {out}")
