"""
Configuration for the LinkedIn pipeline.
Edit the AUTHOR section to match your profile.
API keys come from environment variables (GitHub Secrets in production).
"""

import os

# ───────── AUTHOR PROFILE ─────────
# This shapes every prompt. Be specific.

AUTHOR = {
    "name": "Kalyani Dhusia, Ph.D.",
    "title": "Computational Biologist",
    "affiliation": "UAMS Winthrop P. Rockefeller Cancer Institute",
    "tagline": "Making dumb machines solve biological problems.",
    "expertise": [
        "Proteomics (DIA, DDA, TMT)",
        "Multi-omics integration",
        "Machine learning for biology",
        "Protein-protein interactions",
        "Cancer genomics",
        "Single-cell genomics",
        "Spatial transcriptomics",
        "Flow / mass cytometry",
        "SomaScan analysis",
    ],
    "audience": "Bioinformatics students, early-career computational biologists, ML-curious wet-lab scientists",
    "voice_traits": [
        "Warm and approachable, never preachy",
        "Tells short personal stories from the bench / from the terminal",
        "Uses 'I' and 'we', not 'one should'",
        "Comfortable being uncertain — 'I'm still figuring this out'",
        "Light humor, no clickbait",
        "Specific numbers and tool names beat vague claims",
        "Buzzword-light: '90% buzzword-free' is the bar",
    ],
}

# ───────── LLM SETTINGS ─────────
# The script auto-picks based on which key is set. Priority: Anthropic > Gemini > OpenAI.

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "auto")

LLM_MODELS = {
    "anthropic": "claude-sonnet-4-5",
    "gemini": "gemini-2.0-flash",
    "openai": "gpt-4o-mini",
}

# ───────── POST TYPE ROTATION ─────────
# Weights for the random pick. Higher = more often.
# Bumped Type 2 a bit because tips travel well on LinkedIn.

TYPE_WEIGHTS = {
    "type1_update": 1.0,
    "type2_tip": 1.4,
    "type3_visual": 1.0,
}

# Rolling memory: don't repeat the same type 2 weeks in a row.
AVOID_REPEATS = True

# ───────── SOURCES ─────────

BIORXIV_FEEDS = [
    # bioRxiv subject RSS feeds. Add/remove freely.
    "https://connect.biorxiv.org/biorxiv_xml.php?subject=bioinformatics",
    "https://connect.biorxiv.org/biorxiv_xml.php?subject=systems_biology",
    "https://connect.biorxiv.org/biorxiv_xml.php?subject=cancer_biology",
]

GITHUB_TRENDING_URL = "https://github.com/trending/python?since=weekly"

# How many candidate items to feed the LLM. Too few = repetitive picks, too many = bigger prompt.
MAX_CANDIDATES_PER_SOURCE = 10

# ───────── OUTPUT ─────────

DRAFTS_DIR = "drafts"
TEMPLATES_DIR = "templates"
HEADSHOT_FILE = "templates/headshot.png"

# Image card dimensions (LinkedIn likes 1200x1200 for square posts).
CARD_SIZE = (1200, 1200)
CARD_BG = "#0F1A2E"      # Deep navy
CARD_ACCENT = "#E63946"  # Coral red, picks up the shirt
CARD_TEXT = "#F1F1F1"
