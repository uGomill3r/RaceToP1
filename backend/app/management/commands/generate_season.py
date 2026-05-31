"""
generate_season — Django management command.

Usage:
    python manage.py generate_season 2023
    python manage.py generate_season 2021 2022 2023
    python manage.py generate_season --years 2018 2019 2020 2021 2022 2023

Output goes to ../frontend/data/{year}.json by default,
or to a custom path via --output-dir.
"""

import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

# Resolve the default output dir relative to this file's location
_HERE = Path(__file__).resolve()
_DEFAULT_OUTPUT = _HERE.parents[5] / "RaceToP1" / "frontend" / "data"


class Command(BaseCommand):
    help = "Fetch F1 season results and generate static JSON data files."

    def add_arguments(self, parser):
        parser.add_argument(
            "years",
            nargs="*",
            type=int,
            metavar="YEAR",
            help="One or more season years (e.g. 2021 2022 2023).",
        )
        parser.add_argument(
            "--years",
            dest="years_flag",
            nargs="+",
            type=int,
            metavar="YEAR",
            help="Alternative way to pass years (e.g. --years 2021 2022).",
        )
        parser.add_argument(
            "--output-dir",
            default=str(_DEFAULT_OUTPUT),
            help=f"Directory to write JSON files. Default: {_DEFAULT_OUTPUT}",
        )

    def handle(self, *args, **options):
        # Merge positional and flag years, deduplicate, sort
        years = sorted(set(
            (options.get("years") or []) + (options.get("years_flag") or [])
        ))

        if not years:
            raise CommandError(
                "Provide at least one year. Example: python manage.py generate_season 2023"
            )

        output_dir = Path(options["output_dir"])
        self.stdout.write(f"Output directory: {output_dir}\n")

        # Late import so Django settings are already configured
        from app.f1_data import save_season_json, update_seasons_index

        success, failed = [], []

        for year in years:
            self.stdout.write(f"\n{'─' * 40}")
            self.stdout.write(f" Processing season {year} …")
            self.stdout.write(f"{'─' * 40}\n")
            try:
                out_path = save_season_json(year, output_dir)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {year} → {out_path}")
                )
                success.append(year)
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(
                    self.style.ERROR(f"✗ {year} failed: {exc}")
                )
                failed.append(year)

        if success:
            seasons_path = update_seasons_index(success, output_dir)
            self.stdout.write(
                self.style.SUCCESS(f"\n✓ seasons.json actualizado → {seasons_path}")
            )

        self.stdout.write(f"\n{'═' * 40}")
        self.stdout.write(
            self.style.SUCCESS(f"Done. Success: {success}") if not failed
            else self.style.WARNING(f"Done. Success: {success} | Failed: {failed}")
        )

        if failed:
            sys.exit(1)