from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import sys

import gpxpy
import simplekml

ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "input"
OUTPUT_DIR = ROOT / "output"
ARCHIVE_DIR = ROOT / "archive"

SUPPORTED_SUFFIXES = {".gpx", ".json"}


def ensure_directories() -> None:
    """Create required folders if they do not exist."""
    for folder in (INPUT_DIR, OUTPUT_DIR, ARCHIVE_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def get_input_files() -> list[Path]:
    """
    Find supported input files once.

    Using iterdir() and suffix.lower() avoids processing the same GPX twice
    on Windows, where '*.gpx' and '*.GPX' can refer to the same file.
    """
    return sorted(
        (
            file
            for file in INPUT_DIR.iterdir()
            if file.is_file() and file.suffix.lower() in SUPPORTED_SUFFIXES
        ),
        key=lambda file: file.name.lower(),
    )


def format_datetime(value: datetime | None) -> str | None:
    """Return an ISO 8601 datetime string."""
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.isoformat()


def parse_google_time(value: str | None) -> datetime | None:
    """Parse Google Timeline's ISO-8601 time value."""
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def format_google_time(value: str | None) -> str:
    """Return a readable Google Timeline timestamp."""
    return value or "N/A"


def duration_text(start_time: str | None, end_time: str | None) -> str:
    """Calculate a readable duration from two Google Timeline timestamps."""
    start = parse_google_time(start_time)
    end = parse_google_time(end_time)

    if start is None or end is None:
        return "N/A"

    seconds = int((end - start).total_seconds())

    if seconds < 0:
        return "N/A"

    hours, remaining = divmod(seconds, 3600)
    minutes, seconds = divmod(remaining, 60)

    if hours:
        return f"{hours}h {minutes}m {seconds}s"

    if minutes:
        return f"{minutes}m {seconds}s"

    return f"{seconds}s"


def parse_geo(value: str | None) -> tuple[float, float] | None:
    """
    Convert Google Timeline's 'geo:latitude,longitude' format into
    KML coordinate order: (longitude, latitude).
    """
    if not isinstance(value, str) or not value.startswith("geo:"):
        return None

    try:
        latitude, longitude = value[4:].split(",", maxsplit=1)
        return float(longitude), float(latitude)
    except ValueError:
        return None


def set_time_span(
    feature,
    start_time: str | None,
    end_time: str | None,
) -> None:
    """Attach a KML TimeSpan to a feature if timestamps are available."""
    if start_time:
        feature.timespan.begin = start_time

    if end_time:
        feature.timespan.end = end_time


# -------------------------------------------------------------------
# GPX -> KML
# -------------------------------------------------------------------

def add_gpx_tracks(
    folder: simplekml.Folder,
    gpx_file: Path,
    gpx,
) -> int:
    """Create KML route lines from GPX track segments."""
    segment_count = 0

    for track_number, track in enumerate(gpx.tracks, start=1):
        track_name = track.name or f"Track {track_number}"

        for segment_number, segment in enumerate(track.segments, start=1):
            points = segment.points

            if not points:
                continue

            segment_count += 1

            start_time = format_datetime(points[0].time) or "N/A"
            end_time = format_datetime(points[-1].time) or "N/A"

            line = folder.newlinestring(
                name=f"{gpx_file.stem} - {track_name} - Segment {segment_number}",
                description=(
                    f"<b>Track points:</b> {len(points)}<br/>"
                    f"<b>Start:</b> {start_time}<br/>"
                    f"<b>End:</b> {end_time}"
                ),
            )

            line.coords = [
                (
                    point.longitude,
                    point.latitude,
                    point.elevation if point.elevation is not None else 0,
                )
                for point in points
            ]

            line.style.linestyle.color = simplekml.Color.red
            line.style.linestyle.width = 4
            line.altitudemode = simplekml.AltitudeMode.clamptoground

    return segment_count


def add_gpx_waypoints(
    folder: simplekml.Folder,
    gpx,
) -> int:
    """Create KML points from GPX waypoints."""
    waypoint_count = 0

    for waypoint_number, point in enumerate(gpx.waypoints, start=1):
        waypoint_count += 1

        waypoint_name = point.name or f"Waypoint {waypoint_number}"
        waypoint_time = format_datetime(point.time) or "N/A"

        elevation = (
            f"{point.elevation:.2f} m"
            if point.elevation is not None
            else "N/A"
        )

        marker = folder.newpoint(
            name=waypoint_name,
            description=(
                f"<b>Time:</b> {waypoint_time}<br/>"
                f"<b>Latitude:</b> {point.latitude:.6f}<br/>"
                f"<b>Longitude:</b> {point.longitude:.6f}<br/>"
                f"<b>Elevation:</b> {elevation}"
            ),
            coords=[
                (
                    point.longitude,
                    point.latitude,
                    point.elevation if point.elevation is not None else 0,
                )
            ],
        )

        if point.time is not None:
            marker.timestamp.when = format_datetime(point.time)

        marker.style.iconstyle.icon.href = (
            "http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png"
        )

    return waypoint_count


def convert_gpx_to_kml(gpx_file: Path) -> tuple[Path, str]:
    """Convert one GPX file into one KML file."""
    with gpx_file.open("r", encoding="utf-8") as file:
        gpx = gpxpy.parse(file)

    kml = simplekml.Kml(name=gpx_file.stem)
    document = kml.newdocument(name=gpx_file.stem)

    tracks_folder = document.newfolder(name="Tracks")
    waypoints_folder = document.newfolder(name="Waypoints")

    segment_count = add_gpx_tracks(tracks_folder, gpx_file, gpx)
    waypoint_count = add_gpx_waypoints(waypoints_folder, gpx)

    if segment_count == 0 and waypoint_count == 0:
        raise ValueError("The GPX file contains no tracks or waypoints.")

    output_file = OUTPUT_DIR / f"{gpx_file.stem}.kml"
    kml.save(str(output_file))

    if not output_file.exists() or output_file.stat().st_size == 0:
        raise RuntimeError("The KML file was not created successfully.")

    details = (
        f"GPX segments converted: {segment_count}\n"
        f"  GPX waypoints converted: {waypoint_count}"
    )

    return output_file, details


# -------------------------------------------------------------------
# Google Timeline JSON -> KML
# -------------------------------------------------------------------

def add_timeline_activity(
    folder: simplekml.Folder,
    index: int,
    item: dict,
) -> bool:
    """
    Add one Google Timeline activity as a KML line.

    The source JSON only contains activity start/end coordinates.
    The output line is therefore a straight line, not the actual road route.
    """
    activity = item.get("activity")

    if not isinstance(activity, dict):
        return False

    start_coordinate = parse_geo(activity.get("start"))
    end_coordinate = parse_geo(activity.get("end"))

    if start_coordinate is None or end_coordinate is None:
        return False

    start_time = item.get("startTime")
    end_time = item.get("endTime")

    candidate = activity.get("topCandidate", {})

    if not isinstance(candidate, dict):
        candidate = {}

    transport_type = candidate.get("type", "Unknown activity")
    probability = candidate.get("probability", "N/A")
    distance_meters = activity.get("distanceMeters", "N/A")

    try:
        distance_text = f"{float(distance_meters) / 1000:.2f} km"
    except (ValueError, TypeError):
        distance_text = f"{distance_meters} m"

    line = folder.newlinestring(
        name=f"Activity {index}: {transport_type}",
        description=(
            f"<b>Type:</b> {transport_type}<br/>"
            f"<b>Start:</b> {format_google_time(start_time)}<br/>"
            f"<b>End:</b> {format_google_time(end_time)}<br/>"
            f"<b>Duration:</b> {duration_text(start_time, end_time)}<br/>"
            f"<b>Distance:</b> {distance_text}<br/>"
            f"<b>Activity probability:</b> {probability}<br/><br/>"
            f"<i>Note: Google Timeline JSON includes only start and end "
            f"coordinates for this activity. This line is not the actual "
            f"road, rail, or walking route.</i>"
        ),
        coords=[start_coordinate, end_coordinate],
    )

    set_time_span(line, start_time, end_time)
    line.style.linestyle.color = simplekml.Color.blue
    line.style.linestyle.width = 4
    line.altitudemode = simplekml.AltitudeMode.clamptoground

    return True


def add_timeline_visit(
    folder: simplekml.Folder,
    index: int,
    item: dict,
) -> bool:
    """Add one Google Timeline visit as a KML point."""
    visit = item.get("visit")

    if not isinstance(visit, dict):
        return False

    candidate = visit.get("topCandidate", {})

    if not isinstance(candidate, dict):
        candidate = {}

    coordinate = parse_geo(candidate.get("placeLocation"))

    if coordinate is None:
        return False

    start_time = item.get("startTime")
    end_time = item.get("endTime")

    semantic_type = candidate.get("semanticType", "Unknown")
    place_id = candidate.get("placeID", "N/A")
    probability = visit.get("probability", "N/A")

    marker = folder.newpoint(
        name=f"Visit {index}: {semantic_type}",
        description=(
            f"<b>Type:</b> {semantic_type}<br/>"
            f"<b>Arrival:</b> {format_google_time(start_time)}<br/>"
            f"<b>Departure:</b> {format_google_time(end_time)}<br/>"
            f"<b>Duration:</b> {duration_text(start_time, end_time)}<br/>"
            f"<b>Visit probability:</b> {probability}<br/>"
            f"<b>Google Place ID:</b> {place_id}"
        ),
        coords=[coordinate],
    )

    set_time_span(marker, start_time, end_time)
    marker.style.iconstyle.icon.href = (
        "http://maps.google.com/mapfiles/kml/paddle/ylw-stars.png"
    )

    return True


def convert_timeline_json_to_kml(json_file: Path) -> tuple[Path, str]:
    """Convert a Google Timeline JSON array into one KML file."""
    with json_file.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "This JSON file is not supported. "
            "Expected a top-level array: [ {...}, {...} ]."
        )

    kml = simplekml.Kml(name=json_file.stem)
    document = kml.newdocument(name=json_file.stem)

    activities_folder = document.newfolder(name="Activities (straight lines)")
    visits_folder = document.newfolder(name="Visits")

    activity_count = 0
    visit_count = 0
    skipped_count = 0

    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            skipped_count += 1
            continue

        if "activity" in item:
            if add_timeline_activity(activities_folder, index, item):
                activity_count += 1
            else:
                skipped_count += 1

        elif "visit" in item:
            if add_timeline_visit(visits_folder, index, item):
                visit_count += 1
            else:
                skipped_count += 1

        else:
            skipped_count += 1

    if activity_count == 0 and visit_count == 0:
        raise ValueError(
            "No supported activity or visit records were found in this JSON file."
        )

    output_file = OUTPUT_DIR / f"{json_file.stem}.kml"
    kml.save(str(output_file))

    if not output_file.exists() or output_file.stat().st_size == 0:
        raise RuntimeError("The KML file was not created successfully.")

    details = (
        f"Timeline activities converted: {activity_count}\n"
        f"  Timeline visits converted: {visit_count}\n"
        f"  Timeline records skipped: {skipped_count}"
    )

    return output_file, details


# -------------------------------------------------------------------
# Shared processing
# -------------------------------------------------------------------

def archive_input_file(input_file: Path) -> Path:
    """Move a successfully converted input file to archive/."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_file = ARCHIVE_DIR / f"{input_file.stem}_{timestamp}{input_file.suffix}"

    shutil.move(str(input_file), str(archive_file))

    return archive_file


def convert_file(input_file: Path) -> tuple[Path, str]:
    """Select the correct converter based on the file extension."""
    suffix = input_file.suffix.lower()

    if suffix == ".gpx":
        return convert_gpx_to_kml(input_file)

    if suffix == ".json":
        return convert_timeline_json_to_kml(input_file)

    raise ValueError(f"Unsupported file type: {input_file.suffix}")


def main() -> int:
    ensure_directories()
    input_files = get_input_files()

    if not input_files:
        print("No supported files found in input/.")
        print("Supported formats: .gpx, .json")
        print(f"Input folder: {INPUT_DIR}")
        return 0

    success_count = 0
    failure_count = 0

    print(f"Found {len(input_files)} supported file(s).")
    print("-" * 60)

    for input_file in input_files:
        try:
            output_file, details = convert_file(input_file)
            archive_file = archive_input_file(input_file)

            success_count += 1

            print(f"SUCCESS: {input_file.name}")
            print(f"  Type:    {input_file.suffix.lower()[1:].upper()}")
            print(f"  {details}")
            print(f"  KML:     {output_file.relative_to(ROOT)}")
            print(f"  Archive: {archive_file.relative_to(ROOT)}")

        except Exception as error:
            failure_count += 1

            print(f"FAILED:  {input_file.name}")
            print(f"  Reason: {error}")
            print("  The source file remains in input/.")

        print("-" * 60)

    print(f"Finished. Success: {success_count}, Failed: {failure_count}")

    return 1 if failure_count else 0


if __name__ == "__main__":
    sys.exit(main())