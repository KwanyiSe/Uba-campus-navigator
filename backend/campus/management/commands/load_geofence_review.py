import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from campus.models import Building


class Command(BaseCommand):
    help = (
        "Load draft primary and compensation geofences from the supplied "
        "review data. Use --apply only after visually approving the map."
    )

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Write draft fences to the database.")
        parser.add_argument(
            "--file",
            default=str(Path(__file__).resolve().parents[2] / "data" / "geofence_review_draft.json"),
            help="Path to geofence JSON data.",
        )

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.exists():
            raise CommandError(f"Geofence data file not found: {path}")
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Could not read geofence data: {exc}") from exc

        updated = 0
        missing = []
        for record in records:
            name = str(record.get("name", "")).strip()
            primary = record.get("primary", [])
            compensation = record.get("compensation", [])
            if not name or len(primary) < 3 or len(compensation) < 3:
                self.stderr.write(self.style.WARNING(f"Skipping invalid record: {name or '(unnamed)'}"))
                continue
            matches = list(Building.objects.filter(name__iexact=name))
            if len(matches) != 1:
                missing.append(name)
                self.stderr.write(self.style.WARNING(
                    f"{name}: expected exactly one matching Building, found {len(matches)}"
                ))
                continue
            building = matches[0]
            if options["apply"]:
                building.geofence = primary
                building.compensation_geofence = compensation
                building.geofence_buffer_m = int(record.get("buffer_m", 10))
                building.geofence_status = "draft"
                building.geofence_version = (building.geofence_version or 0) + 1
                building.save(update_fields=[
                    "geofence", "compensation_geofence", "geofence_buffer_m",
                    "geofence_status", "geofence_version",
                ])
            updated += 1
            self.stdout.write(f"{name}: {'saved as draft' if options['apply'] else 'matched (dry run)'}")

        mode = "Saved" if options["apply"] else "Matched"
        self.stdout.write(self.style.SUCCESS(
            f"{mode} {updated} of {len(records)} geofence records."
        ))
        if missing:
            self.stdout.write(self.style.WARNING(
                "Unmatched names: " + ", ".join(missing) +
                ". Rename/map them explicitly before applying."
            ))
        if not options["apply"]:
            self.stdout.write("Dry run only. Add --apply after the map has been reviewed.")
