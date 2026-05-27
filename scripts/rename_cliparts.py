"""
One-time rename of cliparts to short, clean filenames.

Run from project root:
    python scripts/rename_cliparts.py

Safe to run multiple times - skips anything already renamed.
Reports what was renamed, what was skipped, and what's missing.
"""
from pathlib import Path

# Source filename -> target filename
RENAMES = {
    # Tools
    "catppuccin--nextflow.png": "nextflow.png",
    "devicon--docker-wordmark.png": "docker.png",
    # Bioinformatics
    "game-icons--dna2.png": "dna_flow.png",            # DNA-to-dots flow
    "openmoji--dna.png": "dna_helix.png",              # blue DNA helix (image 7)
    "healthicons--cancerous-cell-nuclei.png": "cancer_cells.png",
    "healthicons--skin-cancer-outline.png": "cancer_organ.png",
    "expression.png": "gene_expression.png",           # DNA-to-protein
    "function.png": "gene_function.png",               # DNA with nuts/bolts
    # Concepts
    "noto--brain.png": "brain.png",
    "noto-v1--open-book.png": "open_book.png",
    "streamline-emojis--open-book.png": "open_book_color.png",  # alt style
    "emojione--file-cabinet.png": "file_cabinet.png",
    "fxemoji--worldmap.png": "world_map.png",
    "game-icons--path-distance.png": "path_distance.png",
    "streamline--money-graph-arrow-increase-ascend-growth-up-arrow-stats-graph-right-grow.png":
        "growth_arrow.png",
    "mdi--graph-bar.png": "bar_chart.png",
    "qlementine-icons--computer-16.png": "computer.png",
    # Optional / cream-square style (rename anyway, manifest will tag them)
    "skill-icons--aiscript-light.png": "ai_script.png",
    "skill-icons--anaconda-light.png": "anaconda.png",
    "skill-icons--gcp-light.png": "gcp.png",
    "skill-icons--linkedin.png": "linkedin.png",
    "skill-icons--linux-light.png": "linux.png",
    # SVG variants (kept separate - we don't load SVG, but rename for tidiness)
    "file-icons--nextflow.svg": "nextflow.svg",
}


def main():
    cliparts_dir = Path(__file__).resolve().parent.parent / "templates" / "cliparts"
    if not cliparts_dir.exists():
        print(f"❌ Directory not found: {cliparts_dir}")
        return

    print(f"Scanning: {cliparts_dir}\n")

    renamed = 0
    skipped_already_renamed = 0
    skipped_missing = 0
    target_exists_conflict = 0

    for old_name, new_name in RENAMES.items():
        old_path = cliparts_dir / old_name
        new_path = cliparts_dir / new_name

        if new_path.exists() and not old_path.exists():
            # Already renamed in a previous run
            skipped_already_renamed += 1
            continue

        if not old_path.exists():
            print(f"⚠ Missing: {old_name}")
            skipped_missing += 1
            continue

        if new_path.exists():
            print(f"⚠ Conflict: {new_name} already exists, skipping rename of {old_name}")
            target_exists_conflict += 1
            continue

        old_path.rename(new_path)
        print(f"✓ {old_name}  →  {new_name}")
        renamed += 1

    # List anything left over that wasn't in the rename map
    all_files = sorted(cliparts_dir.iterdir())
    known_targets = set(RENAMES.values())
    known_sources = set(RENAMES.keys())
    unknown = [f for f in all_files
               if f.is_file()
               and f.name != "manifest.json"
               and f.name not in known_targets
               and f.name not in known_sources]
    if unknown:
        print(f"\n⚠ Unknown files (not in rename map, not in target list):")
        for f in unknown:
            print(f"    {f.name}")

    print(f"\nSummary:")
    print(f"  Renamed: {renamed}")
    print(f"  Already renamed: {skipped_already_renamed}")
    print(f"  Missing source: {skipped_missing}")
    print(f"  Target conflicts: {target_exists_conflict}")
    if unknown:
        print(f"  Unknown files: {len(unknown)}")


if __name__ == "__main__":
    main()
