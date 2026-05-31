#!/usr/bin/env python3
"""
generate_season.py — Standalone script (no Django required).

Usage:
    python scripts/generate_season.py 2023
    python scripts/generate_season.py 2021 2022 2023
    python scripts/generate_season.py 2021 2022 --output-dir ./my/data/dir
"""

import argparse
import logging
import sys
from pathlib import Path

# Allow importing from parent package without installing
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.f1_data import save_season_json, update_seasons_index  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

_DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[2] / "frontend" / "static" / "data"
)


def main():
    parser = argparse.ArgumentParser(
        description="Generate F1 season JSON data files from the Jolpica API."
    )
    parser.add_argument(
        "years",
        nargs="+",
        type=int,
        metavar="YEAR",
        help="One or more season years.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(_DEFAULT_OUTPUT),
        metavar="DIR",
        help=f"Destination directory. Default: {_DEFAULT_OUTPUT}",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    success, failed = [], []

    for year in sorted(set(args.years)):
        print(f"\n── Season {year} ──────────────────────────────")
        try:
            out = save_season_json(year, output_dir)
            print(f"✓  Written to {out}")
            success.append(year)
        except Exception as exc:  # noqa: BLE001
            print(f"✗  Failed: {exc}", file=sys.stderr)
            failed.append(year)

    print(f"\n{'═' * 48}")
    print(f"Success: {success}")
    if success:
        seasons_path = update_seasons_index(success, output_dir)
        print(f"✓  seasons.json actualizado → {seasons_path}")
    if failed:
        print(f"Failed:  {failed}", file=sys.stderr)
        sys.exit(1)
    print("All done 🏁")


if __name__ == "__main__":
    main()