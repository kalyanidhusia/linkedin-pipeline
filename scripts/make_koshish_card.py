"""
Render a Type 4 'Koshish note' card: clean typography on a subtle ruled
notebook background, with highlighter accents and the Koshish signature.

Design notes:
  - 1080 x 1350 (4:5 portrait — LinkedIn's max real estate)
  - Off-white paper background with very subtle texture
  - Faint blue horizontal rules
  - Thin red margin line on the left
  - Title in a hand-lettered font (Caveat on Mac, Lora-Italic fallback)
  - Numbered sections, each with a colored highlighter swoosh behind the section title
  - Bullet points in clean sans-serif body font (Poppins-Medium)
  - Bottom-right signature: handwritten cursive '~ Kalyani Dhusia, Ph.D.'
    plus 'Koshish — an attempt, an effort.' in smaller italic
"""

import random
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Dimensions
CARD_W = 1080
CARD_H = 1350

# Paper palette
PAPER_BASE = (252, 250, 244)   # warm off-white
PAPER_SHADOW = (240, 236, 224) # very faint shadow tint
INK_BLACK = (28, 32, 40)
INK_BLUE = (38, 56, 118)       # title color - deeper, more saturated notebook ink
INK_DARK = (28, 32, 40)        # body text - slightly darker for contrast
RULE_BLUE = (200, 218, 240)    # faint ruled lines
MARGIN_RED = (220, 100, 100)   # left margin line
SIG_GREY = (90, 95, 105)       # subtle signature color

# Doodles directory - drop PNG files with transparent backgrounds here
# and the script will randomly place 1-2 per card in non-text areas.
DOODLES_DIR_NAME = "doodles"  # under templates/

# Cliparts directory - tool/topic icons placed ON THE NOTEBOOK PAGE in backdrop mode.
# These ride on top of the eraser (so they survive page-wiping) but underneath text.
# Drop PNGs of Docker, Nextflow, DNA, microscope, file cabinet, etc here.
CLIPARTS_DIR_NAME = "cliparts"  # under templates/

# Backdrop directory - drop full-card backdrop PNGs here (e.g., Gemini-generated
# photo-realistic notebook scenes). If any exist, one is chosen per card and used
# as the base. If none exist, the script falls back to drawn-paper rendering.
BACKDROPS_DIR_NAME = "backdrops"  # under templates/

# Page region within the backdrop image - bounds of the PHYSICAL notebook page.
# Used only when we need to know where the page is (e.g., not used for an eraser
# anymore - the backdrop should arrive with an already-empty page).
PAGE_REGION = {
    "left_frac": 0.15,
    "right_frac": 0.79,
    "top_frac": 0.15,
    "bottom_frac": 0.93,
}

# Text column bounds within the card (in BACKDROP mode).
# These fractions are applied to the full card dimensions (1080 x 1350).

# Layout mode for backdrop rendering.
#   "narrow" = original narrow text column + vertical clipart stack on right
#   "wide"   = text spans most of page, cliparts placed inline beside sections
LAYOUT_MODE = "wide"

# Text column bounds for "narrow" mode (left half of page, clipart column to right)
TEXT_COLUMN = {
    "left_frac": 0.21,    # right of the spiral binding
    "right_frac": 0.66,   # leaves the right column for cliparts
    "top_frac": 0.16,     # just below page top
    "bottom_frac": 0.92,  # leaves room for signature at very bottom
}

# Text column bounds for "wide" mode (spans most of the notebook page)
TEXT_COLUMN_WIDE = {
    "left_frac": 0.18,
    "right_frac": 0.75,
    "top_frac": 0.18,
    "bottom_frac": 0.89,
}

# Inline clipart placement (wide mode): cliparts placed right of text at each
# section's y-position. Bounds define the horizontal strip they live in.
INLINE_CLIPART = {
    "left_frac": 0.65,
    "right_frac": 0.76,
    "max_size_px": 110,
}

# Clipart column bounds (right of the text column, within the notebook page)
CLIPART_COLUMN = {
    "left_frac": 0.60,
    "right_frac": 0.77,
    "top_frac": 0.14,
    "bottom_frac": 0.76,  # leaves signature slot below
}

# Tilt to match the notebook's angle in the backdrop photo.
# All backdrops should be generated with the notebook at this same angle.
# Wide mode uses a more pronounced tilt to match the "handwritten on the page"
# reference style.
NOTEBOOK_TILT_DEG = -10.0

# Paper color sampled from typical notebook-page backdrops
BACKDROP_PAGE_COLOR = (238, 234, 228)

# Highlighter palette - punchier, more saturated than soft pastels
HIGHLIGHTS = [
    (255, 220, 90, 190),   # yellow - more vivid
    (255, 160, 180, 190),  # pink - deeper
    (140, 220, 160, 190),  # green - more chroma
    (140, 195, 250, 190),  # blue - punchier
    (220, 170, 250, 190),  # purple - richer
]

# Stronger closing-note yellow (warm and inviting)
CLOSING_YELLOW = (255, 215, 80, 200)


def _font_candidates(style: str) -> list[str]:
    """Platform-aware font paths."""
    if sys.platform == "darwin":
        # User fonts directory - portable across users
        user_fonts = str(Path.home() / "Library" / "Fonts")
        candidates = {
            "title_hand": [
                # Caveat (install from Google Fonts) gives the best handwritten feel
                f"{user_fonts}/Caveat-Bold.ttf",
                f"{user_fonts}/Caveat-VariableFont_wght.ttf",
                f"{user_fonts}/Caveat-Medium.ttf",
                "/Library/Fonts/Caveat-Bold.ttf",
                "/System/Library/Fonts/Supplemental/Marker Felt.ttc",
                "/Library/Fonts/Marker Felt.ttc",
                # Fall back to a script-y system font
                "/System/Library/Fonts/Supplemental/SnellRoundhand.ttc",
            ],
            "body_bold": [
                f"{user_fonts}/Poppins-Bold.ttf",
                "/Library/Fonts/Poppins-Bold.ttf",
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/System/Library/Fonts/HelveticaNeue.ttc",
            ],
            "body": [
                f"{user_fonts}/Poppins-Medium.ttf",
                f"{user_fonts}/Poppins-Regular.ttf",
                "/Library/Fonts/Poppins-Medium.ttf",
                "/Library/Fonts/Poppins-Regular.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/HelveticaNeue.ttc",
            ],
            "section_hand": [
                f"{user_fonts}/Caveat-Bold.ttf",
                f"{user_fonts}/Caveat-VariableFont_wght.ttf",
                f"{user_fonts}/Caveat-Medium.ttf",
                "/Library/Fonts/Caveat-Bold.ttf",
                f"{user_fonts}/Poppins-Bold.ttf",
                "/Library/Fonts/Poppins-Bold.ttf",
            ],
            "signature_script": [
                "/System/Library/Fonts/Supplemental/SnellRoundhand.ttc",
                "/Library/Fonts/Snell Roundhand.ttc",
                "/System/Library/Fonts/Supplemental/Apple Chancery.ttf",
            ],
            "tagline_italic": [
                "/Library/Fonts/Poppins-Italic.ttf",
                "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
            ],
        }
        return candidates.get(style, candidates["body"])

    if sys.platform.startswith("linux"):
        return {
            "title_hand": [
                "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf",
                "/usr/share/fonts/truetype/google-fonts/Poppins-BoldItalic.ttf",
            ],
            "body_bold": [
                "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
            ],
            "body": [
                "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf",
                "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf",
            ],
            "section_hand": [
                "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf",
                "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
            ],
            "signature_script": [
                "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf",
            ],
            "tagline_italic": [
                "/usr/share/fonts/truetype/google-fonts/Poppins-Italic.ttf",
            ],
        }.get(style, [])

    return {
        "title_hand": [r"C:\Windows\Fonts\segoesc.ttf"],
        "body_bold": [r"C:\Windows\Fonts\arialbd.ttf"],
        "body": [r"C:\Windows\Fonts\arial.ttf"],
        "section_hand": [r"C:\Windows\Fonts\segoesc.ttf"],
        "signature_script": [r"C:\Windows\Fonts\segoesc.ttf"],
        "tagline_italic": [r"C:\Windows\Fonts\ariali.ttf"],
    }.get(style, [])


def _load_font(size: int, style: str = "body") -> ImageFont.FreeTypeFont:
    for path in _font_candidates(style):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
          max_width: int) -> list[str]:
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


def _find_backdrops_dir() -> Path | None:
    """Locate templates/backdrops folder relative to the script."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / "templates" / BACKDROPS_DIR_NAME,
        script_dir / "templates" / BACKDROPS_DIR_NAME,
    ]
    return next((p for p in candidates if p.exists() and p.is_dir()), None)


def _list_backdrops() -> list[Path]:
    """Return all backdrop PNGs available for selection."""
    bd_dir = _find_backdrops_dir()
    if bd_dir is None:
        return []
    files = list(bd_dir.glob("*.png")) + list(bd_dir.glob("*.PNG"))
    return sorted(files)


def _page_bounds() -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) of the notebook-page region within the card."""
    left = int(CARD_W * PAGE_REGION["left_frac"])
    right = int(CARD_W * PAGE_REGION["right_frac"])
    top = int(CARD_H * PAGE_REGION["top_frac"])
    bottom = int(CARD_H * PAGE_REGION["bottom_frac"])
    return left, top, right, bottom


def _make_backdrop_canvas(rng: random.Random) -> tuple[Image.Image, bool]:
    """Load a random backdrop. The backdrop must arrive with an already-empty
    notebook page - no eraser is applied. Falls back to drawn paper if no
    backdrops are available."""
    backdrops = _list_backdrops()
    if not backdrops:
        return _make_paper(rng), False

    backdrop_path = rng.choice(backdrops)
    try:
        bd = Image.open(backdrop_path).convert("RGB")
    except Exception as e:
        print(f"  ⚠ Could not load backdrop {backdrop_path.name}: {e}")
        return _make_paper(rng), False

    bd = bd.resize((CARD_W, CARD_H), Image.LANCZOS)
    return bd, True


def _make_paper(rng: random.Random) -> Image.Image:
    """Subtle off-white paper with very faint texture noise."""
    img = Image.new("RGB", (CARD_W, CARD_H), PAPER_BASE)

    # Subtle noise texture
    noise = Image.new("L", (CARD_W // 4, CARD_H // 4))
    nload = noise.load()
    for y in range(noise.height):
        for x in range(noise.width):
            nload[x, y] = rng.randint(245, 255)
    noise = noise.resize((CARD_W, CARD_H), Image.BILINEAR)
    noise = noise.filter(ImageFilter.GaussianBlur(0.5))

    # Apply noise as a multiplicative overlay (very subtle)
    img_rgba = img.convert("RGBA")
    noise_rgba = Image.merge("RGBA", [noise, noise, noise, Image.new("L", noise.size, 30)])
    img_rgba = Image.alpha_composite(img_rgba, noise_rgba)
    return img_rgba.convert("RGB")


def _draw_ruled_lines(img: Image.Image, top: int, bottom: int) -> None:
    """Faint horizontal blue rules, like notebook paper."""
    draw = ImageDraw.Draw(img)
    line_spacing = 56
    y = top
    while y < bottom:
        draw.line([(60, y), (CARD_W - 60, y)], fill=RULE_BLUE, width=1)
        y += line_spacing


def _draw_margin(img: Image.Image) -> None:
    """Thin red margin line on the left."""
    draw = ImageDraw.Draw(img)
    x = 110
    draw.line([(x, 40), (x, CARD_H - 40)], fill=MARGIN_RED, width=2)


def _draw_highlighter_swoosh(img: Image.Image, x: int, y: int, w: int, h: int,
                             color: tuple, rng: random.Random) -> None:
    """A soft-edged highlighter rectangle, slightly rotated and rough at edges."""
    # Render onto a temp RGBA, blur, paste
    swoosh = Image.new("RGBA", (w + 40, h + 30), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(swoosh)
    # Slightly tapered rectangle
    sdraw.rounded_rectangle([10, 10, w + 30, h + 20], radius=8, fill=color)
    swoosh = swoosh.filter(ImageFilter.GaussianBlur(radius=4))
    # Small rotation for hand-drawn feel
    angle = rng.uniform(-1.5, 1.5)
    swoosh = swoosh.rotate(angle, resample=Image.BICUBIC, expand=True)
    img.paste(swoosh, (x - 20, y - 15), swoosh)


def _place_doodles(img: Image.Image, occupied: list[tuple[int, int, int, int]],
                   rng: random.Random) -> None:
    """Randomly place 1-2 doodles from templates/doodles/ in non-text areas.

    occupied: list of (x1, y1, x2, y2) bounding boxes where text was drawn.
    Silently does nothing if no doodles are available.

    Drop PNGs (transparent background ideal) into templates/doodles/ and the
    script picks 1-2 per card and places them in safe corner/margin zones.
    """
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / "templates" / DOODLES_DIR_NAME,
        script_dir / "templates" / DOODLES_DIR_NAME,
    ]
    doodles_dir = next((p for p in candidates if p.exists() and p.is_dir()), None)
    if doodles_dir is None:
        return

    doodle_files = list(doodles_dir.glob("*.png")) + list(doodles_dir.glob("*.PNG"))
    if not doodle_files:
        return

    # Safe placement zones: (x, y, max_w, max_h)
    # Bottom-left is always free (signature is bottom-right). Other zones become
    # available on cards with fewer sections.
    safe_zones = [
        # Bottom-left corner, opposite the signature
        (80, CARD_H - 240, 200, 180),
        # Right margin, between section 2 and 3 (free on 2-3 section cards)
        (CARD_W - 220, int(CARD_H * 0.42), 180, 150),
        # Right margin, near the title (sometimes free)
        (CARD_W - 200, 50, 160, 130),
    ]

    def _overlaps(box1, box2):
        x1, y1, x2, y2 = box1
        a1, b1, a2, b2 = box2
        return not (x2 < a1 or a2 < x1 or y2 < b1 or b2 < y1)

    def _zone_to_box(z):
        x, y, w, h = z
        return (x, y, x + w, y + h)

    free_zones = [z for z in safe_zones
                  if not any(_overlaps(_zone_to_box(z), occ) for occ in occupied)]
    if not free_zones:
        return

    n_doodles = 1 if (len(free_zones) < 2 or rng.random() < 0.5) else 2
    chosen_zones = rng.sample(free_zones, min(n_doodles, len(free_zones)))
    chosen_doodles = rng.sample(doodle_files, min(n_doodles, len(doodle_files)))

    for zone, doodle_path in zip(chosen_zones, chosen_doodles):
        try:
            doodle = Image.open(doodle_path).convert("RGBA")
        except Exception:
            continue
        zx, zy, zw, zh = zone
        ratio = min(zw / doodle.width, zh / doodle.height)
        new_w = max(1, int(doodle.width * ratio * 0.9))
        new_h = max(1, int(doodle.height * ratio * 0.9))
        doodle = doodle.resize((new_w, new_h), Image.LANCZOS)
        angle = rng.uniform(-6, 6)
        doodle = doodle.rotate(angle, resample=Image.BICUBIC, expand=True)
        px = zx + (zw - doodle.width) // 2
        py = zy + (zh - doodle.height) // 2
        img.paste(doodle, (px, py), doodle)


def _load_clipart_manifest() -> dict:
    """Load templates/cliparts/manifest.json. Returns empty dict on any error.

    Manifest format:
      {
        "docker.png": {"tags": ["docker", "containers", "devops"]},
        "dna.png":    {"tags": ["dna", "genomics", "sequencing"]},
        ...
      }
    """
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / "templates" / CLIPARTS_DIR_NAME / "manifest.json",
        script_dir / "templates" / CLIPARTS_DIR_NAME / "manifest.json",
    ]
    manifest_path = next((p for p in candidates if p.exists()), None)
    if not manifest_path:
        return {}
    try:
        import json
        return json.loads(manifest_path.read_text())
    except Exception as e:
        print(f"  ⚠ Could not parse clipart manifest: {e}")
        return {}


def _match_cliparts(hints: list[str], n: int, rng: random.Random) -> list[Path]:
    """Pick up to `n` clipart Paths whose tags overlap with `hints`.
    Falls back to random selection if no matches or no manifest.

    Match scoring: each clipart gets a score = number of tag-hint overlaps.
    Cliparts with score > 0 are preferred. If we need more than the matching
    set provides, top up randomly from the remaining unused cliparts.
    """
    script_dir = Path(__file__).resolve().parent
    candidates_dirs = [
        script_dir.parent / "templates" / CLIPARTS_DIR_NAME,
        script_dir / "templates" / CLIPARTS_DIR_NAME,
    ]
    cliparts_dir = next((p for p in candidates_dirs if p.exists() and p.is_dir()), None)
    if cliparts_dir is None:
        return []

    all_files = list(cliparts_dir.glob("*.png")) + list(cliparts_dir.glob("*.PNG"))
    all_files = [f for f in all_files if f.name != "manifest.json"]
    if not all_files:
        return []

    manifest = _load_clipart_manifest()
    hints_lower = [h.lower().strip() for h in (hints or []) if h]

    # Score each clipart by number of tag-hint overlaps
    scored = []  # list of (score, path)
    for f in all_files:
        entry = manifest.get(f.name, {})
        tags = [t.lower().strip() for t in entry.get("tags", [])]
        score = sum(1 for h in hints_lower if h in tags or any(h in t or t in h for t in tags))
        scored.append((score, f))

    # Separate matches (score > 0) from non-matches
    matches = [p for s, p in scored if s > 0]
    non_matches = [p for s, p in scored if s == 0]

    # Sort matches by score descending, shuffle ties
    rng.shuffle(matches)
    matches.sort(key=lambda p: -next(s for s, q in scored if q == p))

    chosen = matches[:n]
    if len(chosen) < n:
        # Top up randomly from non-matches
        needed = n - len(chosen)
        rng.shuffle(non_matches)
        chosen.extend(non_matches[:needed])
    return chosen


def _place_cliparts_in_column(layer: Image.Image, clipart_paths: list[Path],
                              rng: random.Random) -> int:
    """Place cliparts in the right column (CLIPART_COLUMN bounds) of the page.
    Returns the number of cliparts placed.

    Stacks them vertically with even spacing. Each gets a small random tilt.
    """
    if not clipart_paths:
        return 0

    col_left = int(CARD_W * CLIPART_COLUMN["left_frac"])
    col_right = int(CARD_W * CLIPART_COLUMN["right_frac"])
    col_top = int(CARD_H * CLIPART_COLUMN["top_frac"])
    col_bottom = int(CARD_H * CLIPART_COLUMN["bottom_frac"])
    col_w = col_right - col_left
    col_h = col_bottom - col_top

    n = len(clipart_paths)
    # Each clipart gets a vertical slot. Slot height = col_h / n.
    slot_h = col_h // n
    max_clipart_size = min(int(col_w * 0.9), int(slot_h * 0.7))

    placed = 0
    for i, clipart_path in enumerate(clipart_paths):
        try:
            clip = Image.open(clipart_path).convert("RGBA")
        except Exception:
            continue

        # Scale to fit max_clipart_size while preserving aspect
        ratio = min(max_clipart_size / clip.width, max_clipart_size / clip.height)
        new_w = max(1, int(clip.width * ratio))
        new_h = max(1, int(clip.height * ratio))
        clip = clip.resize((new_w, new_h), Image.LANCZOS)

        # Tilt for hand-placed feel
        angle = rng.uniform(-5, 5)
        clip = clip.rotate(angle, resample=Image.BICUBIC, expand=True)

        # Center horizontally in column, vertically in slot
        slot_top = col_top + i * slot_h
        px = col_left + (col_w - clip.width) // 2
        py = slot_top + (slot_h - clip.height) // 2

        # Composite into the layer
        layer.alpha_composite(clip, (px, py))
        placed += 1

    return placed


def make_card(title: str, sections: list[dict], output_path: str | Path,
              closing_note: str | None = None, seed: int | None = None,
              clipart_hints: list[str] | None = None,
              n_cliparts: int = 3) -> Path:
    """
    Render a Koshish note card.

    sections: list of dicts: {"label": "1. Healthcare", "bullets": [...]}
    clipart_hints: optional list of tag strings the LLM suggests for clipart
                   matching. E.g. ["docker", "workflow", "reproducibility"].
                   The matcher prefers cliparts whose manifest tags overlap
                   these hints. Falls back to random if no manifest/no matches.
    n_cliparts: number of cliparts to place (default 3, max ~3 with current layout).

    Backdrop mode: text and cliparts are rendered to a separate layer, rotated
    by NOTEBOOK_TILT_DEG, and composited onto the backdrop. No eraser is used.

    Paper mode: legacy plain-paper rendering for backward compatibility.
    """
    rng = random.Random(seed) if seed is not None else random.Random()

    # 1. Base canvas: backdrop image if available, else plain paper
    img, used_backdrop = _make_backdrop_canvas(rng)

    if used_backdrop:
        if LAYOUT_MODE == "wide":
            _render_on_backdrop_wide(img, title, sections, closing_note,
                                     clipart_hints or [], rng)
        else:
            _render_on_backdrop(img, title, sections, closing_note,
                                clipart_hints or [], n_cliparts, rng)
    else:
        _render_on_paper(img, title, sections, closing_note, rng)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    return output_path


def _render_on_backdrop(base: Image.Image, title: str, sections: list[dict],
                        closing_note: str | None, clipart_hints: list[str],
                        n_cliparts: int, rng: random.Random) -> None:
    """Render text + cliparts + signature onto a transparent layer, rotate
    by NOTEBOOK_TILT_DEG, and composite onto base in-place."""
    # Build a transparent layer at card dimensions
    layer = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))

    # Text column bounds (left half of the page)
    text_left = int(CARD_W * TEXT_COLUMN["left_frac"])
    text_right = int(CARD_W * TEXT_COLUMN["right_frac"])
    text_top = int(CARD_H * TEXT_COLUMN["top_frac"])
    text_bottom = int(CARD_H * TEXT_COLUMN["bottom_frac"])
    text_width = text_right - text_left

    draw = ImageDraw.Draw(layer)

    # --- TITLE ---
    title_font = _load_font(48, style="title_hand")
    title_lines = _wrap(draw, title, title_font, text_width)
    y = text_top
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_w = bbox[2] - bbox[0]
        # Left-aligned title (centered in narrow column looks weird)
        draw.text((text_left, y), line, font=title_font, fill=INK_BLUE)
        y += 56

    # Title underline (extends across the title's actual width or 240px, whichever larger)
    underline_w = 240
    underline_y = y + 4
    draw.line([(text_left, underline_y),
               (text_left + underline_w - 30, underline_y + 1)],
              fill=INK_BLUE, width=3)
    draw.line([(text_left + underline_w - 40, underline_y + 1),
               (text_left + underline_w, underline_y - 1)],
              fill=INK_BLUE, width=3)
    y += 32

    # --- SECTIONS ---
    section_font = _load_font(32, style="section_hand")
    bullet_font = _load_font(26, style="")
    bullet_indent = 32
    section_advance = 44
    bullet_advance = 34
    section_gap = 8

    max_content_y = text_bottom - 30  # leave room for graceful stop

    for i, sec in enumerate(sections):
        if y > max_content_y - 60:
            print(f"  ⚠ Stopped rendering at section {i+1} - ran out of vertical space")
            break

        label = sec["label"]
        bullets = sec.get("bullets", [])

        # Highlighter swoosh behind section label
        label_bbox = draw.textbbox((0, 0), label, font=section_font)
        label_w = label_bbox[2] - label_bbox[0]
        label_h = label_bbox[3] - label_bbox[1]
        color = HIGHLIGHTS[i % len(HIGHLIGHTS)]
        _draw_highlighter_swoosh(layer, text_left - 5, y + 4,
                                 label_w + 18, label_h + 8, color, rng)
        draw = ImageDraw.Draw(layer)
        draw.text((text_left, y), label, font=section_font, fill=INK_DARK)
        y += section_advance

        for bullet in bullets:
            if y > max_content_y:
                break
            bullet_text = "• " + bullet
            for line in _wrap(draw, bullet_text, bullet_font,
                              text_width - bullet_indent):
                if y > max_content_y:
                    break
                draw.text((text_left + bullet_indent, y), line,
                          font=bullet_font, fill=INK_DARK)
                y += bullet_advance
        y += section_gap

    # --- CLOSING NOTE ---
    if closing_note:
        close_font = _load_font(24, style="body")
        close_lines = _wrap(draw, closing_note, close_font, text_width - 40)
        estimated_h = len(close_lines) * 32 + 20
        if y + estimated_h <= max_content_y:
            _draw_highlighter_swoosh(layer, text_left, y + 4,
                                     text_width - 10, estimated_h,
                                     CLOSING_YELLOW, rng)
            draw = ImageDraw.Draw(layer)
            y += 14
            for line in close_lines:
                draw.text((text_left + 20, y), line, font=close_font, fill=INK_DARK)
                y += 32
        else:
            print(f"  ⚠ Closing note skipped (overflow)")

    # --- CLIPARTS ---
    if n_cliparts > 0:
        chosen = _match_cliparts(clipart_hints, n_cliparts, rng)
        if chosen:
            placed = _place_cliparts_in_column(layer, chosen, rng)
            print(f"  ✓ Placed {placed} clipart(s) (hints: {clipart_hints})")
        elif clipart_hints:
            print(f"  ⓘ No cliparts available (hints were: {clipart_hints})")

    # --- SIGNATURE: bottom-right, inside the page ---
    _draw_signature_on_layer(layer)

    # --- ROTATE the whole layer by NOTEBOOK_TILT_DEG (clockwise = negative in PIL) ---
    if NOTEBOOK_TILT_DEG != 0:
        # PIL rotate is counter-clockwise by default; clockwise = negative angle
        layer = layer.rotate(-NOTEBOOK_TILT_DEG, resample=Image.BICUBIC,
                             expand=False, fillcolor=(0, 0, 0, 0))

    # --- COMPOSITE onto the backdrop ---
    base_rgba = base.convert("RGBA")
    base_rgba = Image.alpha_composite(base_rgba, layer)
    # Convert back into the base image's mode and copy pixels
    result = base_rgba.convert("RGB")
    base.paste(result)


def _match_single_clipart(hint: str, rng: random.Random,
                          used: set[Path] | None = None) -> Path | None:
    """Find a single clipart matching the hint string. Returns None if no
    cliparts are available. Avoids returning anything in `used`.

    Prefers cliparts whose tags overlap the hint. For random fallback when
    no tags match, prefers 'line-art' and 'flat-color' styles over 'framed'
    (which have built-in backgrounds and look like stickers, not doodles).
    """
    if not hint:
        return None
    script_dir = Path(__file__).resolve().parent
    candidates_dirs = [
        script_dir.parent / "templates" / CLIPARTS_DIR_NAME,
        script_dir / "templates" / CLIPARTS_DIR_NAME,
    ]
    cliparts_dir = next((p for p in candidates_dirs if p.exists() and p.is_dir()), None)
    if cliparts_dir is None:
        return None
    all_files = [f for f in (list(cliparts_dir.glob("*.png")) + list(cliparts_dir.glob("*.PNG")))
                 if f.name != "manifest.json"]
    if not all_files:
        return None
    used = used or set()
    manifest = _load_clipart_manifest()
    h = hint.lower().strip()
    scored = []
    for f in all_files:
        if f in used:
            continue
        entry = manifest.get(f.name, {})
        tags = [t.lower().strip() for t in entry.get("tags", [])]
        score = sum(1 for t in tags if h == t or h in t or t in h)
        scored.append((score, f))
    if not scored:
        return None

    # Best match first; ties broken randomly
    matches = [p for s, p in scored if s > 0]
    if matches:
        rng.shuffle(matches)
        matches.sort(key=lambda p: -next(s for s, q in scored if q == p))
        return matches[0]

    # No tag matches - fallback to random, but prefer non-"framed" styles.
    # 'framed' cliparts have built-in cream/colored backgrounds that look like
    # stickers on the notebook page. We only pick them if nothing else is left.
    unframed = []
    framed = []
    for s, f in scored:
        if s != 0:
            continue
        style = manifest.get(f.name, {}).get("style", "")
        if style == "framed":
            framed.append(f)
        else:
            unframed.append(f)
    if unframed:
        return rng.choice(unframed)
    if framed:
        return rng.choice(framed)
    return None


def _render_on_backdrop_wide(base: Image.Image, title: str, sections: list[dict],
                             closing_note: str | None, clipart_hints: list[str],
                             rng: random.Random) -> None:
    """Wide-layout backdrop renderer: text spans most of the page, with
    cliparts placed inline beside section labels (LLM picks which sections
    get a clipart via the per-section `clipart` field).

    Tracks each section's y-position so cliparts align with the section
    they belong to.
    """
    layer = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))

    text_left = int(CARD_W * TEXT_COLUMN_WIDE["left_frac"])
    text_right = int(CARD_W * TEXT_COLUMN_WIDE["right_frac"])
    text_top = int(CARD_H * TEXT_COLUMN_WIDE["top_frac"])
    text_bottom = int(CARD_H * TEXT_COLUMN_WIDE["bottom_frac"])
    text_width = text_right - text_left

    draw = ImageDraw.Draw(layer)

    # --- TITLE ---
    title_font = _load_font(54, style="title_hand")
    title_lines = _wrap(draw, title, title_font, text_width)
    y = text_top
    for line in title_lines:
        draw.text((text_left, y), line, font=title_font, fill=INK_BLUE)
        y += 62

    # Title double-underline like image 2 - extra space below text
    underline_y = y + 8
    underline_w = min(text_width - 20, 480)
    draw.line([(text_left, underline_y),
               (text_left + underline_w, underline_y)],
              fill=INK_BLUE, width=3)
    draw.line([(text_left, underline_y + 8),
               (text_left + underline_w, underline_y + 8)],
              fill=INK_BLUE, width=2)
    y += 32

    # --- SECTIONS ---
    # Slightly bigger fonts in wide mode (more horizontal room)
    section_font = _load_font(38, style="section_hand")
    bullet_font = _load_font(30, style="tagline_italic")
    bullet_indent = 38
    section_advance = 50
    bullet_advance = 40
    section_gap = 10
    max_content_y = text_bottom - 30

    # Track each section's y-position for inline clipart placement
    section_positions: list[dict] = []  # [{"y_center": int, "clipart_path": Path or None}, ...]

    used_cliparts: set[Path] = set()

    for i, sec in enumerate(sections):
        if y > max_content_y - 60:
            print(f"  ⚠ Stopped rendering at section {i+1} - ran out of vertical space")
            break

        label = sec["label"]
        bullets = sec.get("bullets", [])
        section_clipart_hint = (sec.get("clipart") or "").strip()

        section_top_y = y
        # Capture the label's vertical position for clipart alignment
        label_y = y

        # Highlighter swoosh behind section label
        label_bbox = draw.textbbox((0, 0), label, font=section_font)
        label_w = label_bbox[2] - label_bbox[0]
        label_h = label_bbox[3] - label_bbox[1]
        color = HIGHLIGHTS[i % len(HIGHLIGHTS)]
        _draw_highlighter_swoosh(layer, text_left - 5, y + 4,
                                 label_w + 18, label_h + 8, color, rng)
        draw = ImageDraw.Draw(layer)
        draw.text((text_left, y), label, font=section_font, fill=INK_DARK)
        y += section_advance

        for bullet in bullets:
            if y > max_content_y:
                break
            bullet_text = "• " + bullet
            for line in _wrap(draw, bullet_text, bullet_font,
                              text_width - bullet_indent):
                if y > max_content_y:
                    break
                draw.text((text_left + bullet_indent, y), line,
                          font=bullet_font, fill=INK_DARK)
                y += bullet_advance

        section_bottom_y = y
        y += section_gap

        # Clipart anchors to the LABEL row, not the section center.
        # This keeps cliparts at consistent y-positions across sections
        # regardless of how many bullets each has.
        label_center_y = label_y + label_h // 2
        clipart_path = None
        if section_clipart_hint:
            clipart_path = _match_single_clipart(section_clipart_hint, rng,
                                                 used=used_cliparts)
            if clipart_path:
                used_cliparts.add(clipart_path)

        section_positions.append({
            "y_center": label_center_y,
            "clipart_path": clipart_path,
            "hint": section_clipart_hint,
        })

    # --- CLOSING NOTE ---
    if closing_note:
        close_font = _load_font(26, style="body")
        close_lines = _wrap(draw, closing_note, close_font, text_width - 40)
        estimated_h = len(close_lines) * 34 + 22
        if y + estimated_h <= max_content_y:
            _draw_highlighter_swoosh(layer, text_left, y + 4,
                                     text_width - 10, estimated_h,
                                     CLOSING_YELLOW, rng)
            draw = ImageDraw.Draw(layer)
            y += 14
            for line in close_lines:
                draw.text((text_left + 20, y), line, font=close_font, fill=INK_DARK)
                y += 34
        else:
            print(f"  ⚠ Closing note skipped (overflow)")

    # --- INLINE CLIPARTS ---
    clip_left = int(CARD_W * INLINE_CLIPART["left_frac"])
    clip_right = int(CARD_W * INLINE_CLIPART["right_frac"])
    clip_band = clip_right - clip_left
    max_size = INLINE_CLIPART["max_size_px"]

    placed = 0
    for pos in section_positions:
        clipart_path = pos["clipart_path"]
        if clipart_path is None:
            continue
        try:
            clip = Image.open(clipart_path).convert("RGBA")
        except Exception:
            continue
        # Scale to fit within max_size and the clip_band width
        target = min(max_size, clip_band)
        ratio = min(target / clip.width, target / clip.height)
        new_w = max(1, int(clip.width * ratio))
        new_h = max(1, int(clip.height * ratio))
        clip = clip.resize((new_w, new_h), Image.LANCZOS)
        # Slight tilt for hand-placed feel
        angle = rng.uniform(-5, 5)
        clip = clip.rotate(angle, resample=Image.BICUBIC, expand=True)
        # Center horizontally in the band, vertically at section's y_center
        px = clip_left + (clip_band - clip.width) // 2
        py = pos["y_center"] - clip.height // 2
        layer.alpha_composite(clip, (px, py))
        placed += 1

    if placed:
        print(f"  ✓ Placed {placed} inline clipart(s)")

    # --- SIGNATURE: bottom-right of text area in wide mode ---
    # Place it just below where content ended, not way down the page
    _draw_signature_on_layer_at(layer, right_x=int(CARD_W * 0.72),
                                bottom_y=min(y + 80, int(CARD_H * 0.86)))

    # --- ROTATE the whole layer by NOTEBOOK_TILT_DEG ---
    if NOTEBOOK_TILT_DEG != 0:
        layer = layer.rotate(-NOTEBOOK_TILT_DEG, resample=Image.BICUBIC,
                             expand=False, fillcolor=(0, 0, 0, 0))

    # --- COMPOSITE onto the backdrop ---
    base_rgba = base.convert("RGBA")
    base_rgba = Image.alpha_composite(base_rgba, layer)
    result = base_rgba.convert("RGB")
    base.paste(result)


def _draw_signature_on_layer(layer: Image.Image) -> None:
    """Draw the Koshish signature at the bottom of the right column."""
    sig_right_x = int(CARD_W * CLIPART_COLUMN["right_frac"])
    sig_bottom_y = int(CARD_H * 0.86)
    _draw_signature_on_layer_at(layer, sig_right_x, sig_bottom_y)


def _draw_signature_on_layer_at(layer: Image.Image, right_x: int, bottom_y: int) -> None:
    """Draw the Koshish signature at a specific right_x / bottom_y on the layer."""
    draw = ImageDraw.Draw(layer)
    sig_font = _load_font(34, style="tagline_italic")
    tagline_font = _load_font(18, style="tagline_italic")

    name = "~ Kalyani Dhusia, Ph.D."
    tagline = "Koshish — an attempt, an effort."

    name_bbox = draw.textbbox((0, 0), name, font=sig_font)
    name_w = name_bbox[2] - name_bbox[0]
    name_h = name_bbox[3] - name_bbox[1]
    tag_bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
    tag_w = tag_bbox[2] - tag_bbox[0]

    name_x = right_x - name_w
    tag_x = right_x - tag_w
    tag_y = bottom_y - 6
    name_y = tag_y - name_h - 12

    draw.text((name_x, name_y), name, font=sig_font, fill=SIG_GREY)
    draw.text((tag_x, tag_y), tagline, font=tagline_font, fill=SIG_GREY)


def _render_on_paper(base: Image.Image, title: str, sections: list[dict],
                     closing_note: str | None, rng: random.Random) -> None:
    """Legacy plain-paper rendering. No tilt, doodles instead of cliparts."""
    # 2. Margin line + 3. Ruled lines
    _draw_margin(base)
    _draw_ruled_lines(base, top=200, bottom=CARD_H - 200)

    content_left = 140
    content_right = CARD_W - 100
    title_top = 90
    sig_bottom_y = CARD_H - 60
    max_content_y = CARD_H - 150

    draw = ImageDraw.Draw(base)
    occupied_zones: list[tuple[int, int, int, int]] = []

    # Title
    title_font = _load_font(64, style="title_hand")
    title_lines = _wrap(draw, title, title_font, CARD_W - 240)
    y = title_top
    title_widest = 0
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_w = bbox[2] - bbox[0]
        title_widest = max(title_widest, line_w)
        x = (CARD_W - line_w) // 2
        draw.text((x, y), line, font=title_font, fill=INK_BLUE)
        y += 70
    title_zone_left = (CARD_W - title_widest) // 2 - 20
    title_zone_right = title_zone_left + title_widest + 40
    occupied_zones.append((title_zone_left, title_top - 10, title_zone_right, y + 20))

    underline_y = y + 6
    underline_left = (CARD_W - 320) // 2
    underline_right = underline_left + 320
    draw.line([(underline_left, underline_y),
               (underline_right - 50, underline_y + 1)],
              fill=INK_BLUE, width=4)
    draw.line([(underline_right - 70, underline_y + 1),
               (underline_right, underline_y - 1)],
              fill=INK_BLUE, width=4)
    y += 50

    # Sections
    section_font = _load_font(44, style="section_hand")
    #bullet_font = _load_font(38, style="body")
    bullet_font = _load_font(38, style="tagline_italic")
    sections_top = y
    bullet_indent = 50

    for i, sec in enumerate(sections):
        label = sec["label"]
        bullets = sec.get("bullets", [])
        label_bbox = draw.textbbox((0, 0), label, font=section_font)
        label_w = label_bbox[2] - label_bbox[0]
        label_h = label_bbox[3] - label_bbox[1]
        color = HIGHLIGHTS[i % len(HIGHLIGHTS)]
        _draw_highlighter_swoosh(base, content_left - 5, y + 8,
                                 label_w + 20, label_h + 10, color, rng)
        draw = ImageDraw.Draw(base)
        draw.text((content_left, y), label, font=section_font, fill=INK_DARK)
        y += 60
        for bullet in bullets:
            bullet_text = "• " + bullet
            for line in _wrap(draw, bullet_text, bullet_font,
                              content_right - content_left - bullet_indent):
                draw.text((content_left + bullet_indent, y), line,
                          font=bullet_font, fill=INK_DARK)
                y += 48
        y += 16
    occupied_zones.append((content_left - 20, sections_top, content_right + 10, y + 10))

    if closing_note:
        close_font = _load_font(36, style="body")
        close_lines = _wrap(draw, closing_note, close_font,
                            content_right - content_left - 60)
        box_h = len(close_lines) * 46 + 30
        if y + box_h <= max_content_y:
            _draw_highlighter_swoosh(base, content_left, y + 5,
                                     content_right - content_left - 30, box_h,
                                     CLOSING_YELLOW, rng)
            draw = ImageDraw.Draw(base)
            y += 20
            for line in close_lines:
                draw.text((content_left + 30, y), line, font=close_font, fill=INK_DARK)
                y += 46

    occupied_zones.append((content_left + 100, sig_bottom_y - 130, content_right, sig_bottom_y + 20))
    _place_doodles(base, occupied_zones, rng)
    _draw_signature_at(base, content_right, sig_bottom_y, used_backdrop=False)


def _draw_signature_at(img: Image.Image, right_x: int, bottom_y: int,
                       used_backdrop: bool) -> None:
    """Bottom-right Koshish signature. Position varies based on whether we're
    drawing on a backdrop (inside the page) or plain paper (card corner)."""
    draw = ImageDraw.Draw(img)
    # Slightly smaller for backdrop mode (less space inside the page)
    sig_size = 42 if used_backdrop else 56
    tagline_size = 22 if used_backdrop else 26
    sig_font = _load_font(sig_size, style="signature_script")
    tagline_font = _load_font(tagline_size, style="tagline_italic")

    name = "~ Kalyani Dhusia, Ph.D."
    tagline = "Koshish — an attempt, an effort."

    name_bbox = draw.textbbox((0, 0), name, font=sig_font)
    name_w = name_bbox[2] - name_bbox[0]
    name_h = name_bbox[3] - name_bbox[1]
    tag_bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
    tag_w = tag_bbox[2] - tag_bbox[0]

    name_x = right_x - name_w
    tag_x = right_x - tag_w
    tag_y = bottom_y - 8
    name_y = tag_y - name_h - 18

    draw.text((name_x, name_y), name, font=sig_font, fill=SIG_GREY)
    draw.text((tag_x, tag_y), tagline, font=tagline_font, fill=SIG_GREY)


if __name__ == "__main__":
    # Show which fonts are being used so you can verify Caveat is picked up
    print(f"Detected platform: {sys.platform}")
    print("Font availability check:")
    for style in ["title_hand", "section_hand", "body", "body_bold",
                  "signature_script", "tagline_italic"]:
        found = None
        for path in _font_candidates(style):
            if Path(path).exists():
                found = path
                break
        status = "✓" if found else "✗"
        # Shorten long paths for display
        display = found
        if display and len(display) > 70:
            display = "..." + display[-67:]
        print(f"  {status} {style:18s} → {display or 'NOT FOUND'}")
    print()

    # Mock content based on Kalyani's expertise.
    # Each section optionally has a "clipart" field with a hint - LLM picks
    # which sections deserve a clipart. Sections without get no inline icon.
    sections = [
        {
            "label": "1. The Setup",
            "bullets": [
                "80 patient proteomics samples",
                "Goal: predict treatment response",
            ],
            "clipart": "gene expression",
        },
        {
            "label": "2. The Mistake",
            "bullets": [
                "Normalized before train/test split",
                "Reported 92% AUC, felt great",
            ],
            "clipart": "machine learning",
        },
        {
            "label": "3. The Catch",
            "bullets": [
                "Test set leaked into the normalizer",
                "True AUC after fix: 78%",
            ],
            # No clipart - this section stays clean
        },
        {
            "label": "4. The Lesson",
            "bullets": [
                "Always split before preprocessing",
                "Pipelines beat ad-hoc scripts",
            ],
            "clipart": "workflow",
        },
    ]

    out = make_card(
        title="A data leakage story",
        sections=sections,
        closing_note="The most expensive mistakes are the ones that look like wins.",
        output_path=Path(__file__).parent / "preview_koshish.png",
        seed=11,
        clipart_hints=["machine learning", "docker", "genomics"],
        n_cliparts=3,
    )
    print(f"Saved: {out}")
