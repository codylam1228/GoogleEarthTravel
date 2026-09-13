#!/usr/bin/env python3
"""
repair_kml_track.py - Repair a KML whose track was exported as thousands of
tiny fragments (e.g. one Placemark per GPS point, "Track points: 1"),
by merging all points into clean, time-ordered LineString tracks.

How it works:
  1. Reads every Placemark (LineString or gx:Track) and collects all points
     with timestamps (from the description Start/End, or from <when>).
  2. Sorts all points by time (use --no-sort to keep file order).
  3. Starts a new track whenever the gap between consecutive points exceeds
     --gap-minutes (default 60), so separate trips are not joined by fake
     straight lines.
  4. Writes one repaired KML with one proper LineString per journey.
     With --points-per-part N it also writes part files of max N points.

Usage:
    python repair_kml_track.py paste.txt
    python repair_kml_track.py broken.kml --gap-minutes 30 --out fixed.kml
    python repair_kml_track.py broken.kml --points-per-part 2000 --overlap 1
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from html import escape
from pathlib import Path

KML = "http://www.opengis.net/kml/2.2"
GX = "http://www.google.com/kml/ext/2.2"
NS = {"k": KML, "gx": GX}
ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
SEG_RE = re.compile(r"Segment\s+(\d+)")


def parse_dt(text):
    return datetime.fromisoformat(text.strip().replace("Z", "+00:00"))


def desc_start_end(description):
    start = end = None
    m = re.search(r"Start</b>\s*:?\s*([^<]+)", description)
    if m:
        start = parse_dt(m.group(1))
    m = re.search(r"End</b>\s*:?\s*([^<]+)", description)
    if m:
        end = parse_dt(m.group(1))
    if start is None or end is None:
        found = ISO_RE.findall(description)
        if len(found) >= 2:
            start, end = parse_dt(found[0]), parse_dt(found[-1])
        elif len(found) == 1:
            start = end = parse_dt(found[0])
    return start, end


def read_linestyle(root):
    color, width = "ff0000ff", "4"
    ls = root.find(f".//{{{KML}}}Style/{{{KML}}}LineStyle")
    if ls is not None:
        color = ls.findtext(f"{{{KML}}}color", default=color)
        width = ls.findtext(f"{{{KML}}}width", default=width)
    return color, width


def read_points(path):
    """Collect every track point as {t, coord, seg, idx}. coord stays a raw
    'lon,lat,ele' string to preserve full precision."""
    root = ET.parse(path).getroot()
    color, width = read_linestyle(root)
    points, n_pm, n_single = [], 0, 0
    for idx, pm in enumerate(root.iter(f"{{{KML}}}Placemark")):
        name = pm.findtext("k:name", default="", namespaces=NS)
        desc = pm.findtext("k:description", default="", namespaces=NS)
        m = SEG_RE.search(name)
        seg = int(m.group(1)) if m else idx

        track = pm.find(".//gx:Track", NS)
        if track is not None:
            whens = [parse_dt(w.text) for w in track.findall("k:when", NS)]
            coords = [c.text.strip() for c in track.findall("gx:coord", NS)]
            for t, c in zip(whens, coords):
                points.append({"t": t, "coord": c.replace(" ", ","), "seg": seg, "idx": idx})
            n_pm += 1
            continue

        coord_el = pm.find(".//k:LineString/k:coordinates", NS)
        if coord_el is None or not coord_el.text:
            continue
        coords = coord_el.text.split()
        start, end = desc_start_end(desc)
        n_pm += 1
        if len(coords) == 1:
            n_single += 1
            points.append({"t": start, "coord": coords[0], "seg": seg, "idx": idx})
        else:
            if start is not None and end is not None and end > start:
                step = (end - start) / (len(coords) - 1)
                times = [start + k * step for k in range(len(coords))]
            else:  # no usable times: share the segment's start time (may be None)
                times = [start] * len(coords)
            for t, c in zip(times, coords):
                points.append({"t": t, "coord": c, "seg": seg, "idx": idx})
    return points, color, width, n_pm, n_single


def normalize_timezones(points):
    """If some timestamps are naive, attach the most common offset found."""
    aware = [p["t"].tzinfo for p in points if p["t"] is not None and p["t"].tzinfo is not None]
    ref = max(set(aware), key=aware.count) if aware else None
    if ref is not None:
        for p in points:
            if p["t"] is not None and p["t"].tzinfo is None:
                p["t"] = p["t"].replace(tzinfo=ref)
    return ref


def sort_points(points, no_sort):
    if no_sort:
        return sorted(points, key=lambda p: (p["seg"], p["idx"]))
    far_future = datetime.max.replace(tzinfo=normalize_timezones(points))
    return sorted(points, key=lambda p: (p["t"] is None, p["t"] or far_future, p["seg"], p["idx"]))


def split_journeys(points, gap):
    journeys, current = [], []
    for p in points:
        if (current and p["t"] is not None and current[-1]["t"] is not None
                and p["t"] - current[-1]["t"] > gap):
            journeys.append(current)
            current = []
        current.append(p)
    if current:
        journeys.append(current)
    return journeys


def journey_kml(name, pts, color, width):
    coords = " ".join(p["coord"] for p in pts)
    t0 = next((p["t"] for p in pts if p["t"] is not None), None)
    t1 = next((p["t"] for p in reversed(pts) if p["t"] is not None), None)
    desc = f"<b>Track points</b>: {len(pts)}"
    timespan = ""
    if t0 is not None and t1 is not None:
        desc += f"<br><b>Start</b>: {t0.isoformat()}<br><b>End</b>: {t1.isoformat()}"
        timespan = f"<TimeSpan><begin>{t0.isoformat()}</begin><end>{t1.isoformat()}</end></TimeSpan>"
    return (f'<Placemark><name>{escape(name)}</name>\n'
            f'<description>{escape(desc)}</description>\n'
            f'{timespan}<styleUrl>#track</styleUrl>\n'
            f'<LineString><altitudeMode>clampToGround</altitudeMode>'
            f'<coordinates>{coords}</coordinates></LineString></Placemark>\n')


def kml_document(doc_name, body, color, width):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<kml xmlns="{KML}" xmlns:gx="{GX}">\n<Document>\n'
            f'<name>{escape(doc_name)}</name>\n'
            f'<Style id="track"><LineStyle><color>{color}</color>'
            f'<width>{width}</width></LineStyle></Style>\n'
            f'{body}</Document>\n</kml>\n')


def chunk_ranges(n, size, overlap):
    step, i = size - overlap, 0
    tail_merge = max(overlap, size // 10)
    while True:
        j = min(i + size, n)
        if n - j <= tail_merge:
            j = n
        yield i, j
        if j >= n:
            break
        i += step


def main():
    ap = argparse.ArgumentParser(description="Repair a fragmented KML track into clean LineStrings.")
    ap.add_argument("input", help="input .kml file (any extension works)")
    ap.add_argument("--out", default=None, help="repaired KML path (default: <input>_repaired.kml)")
    ap.add_argument("--gap-minutes", type=float, default=60,
                    help="start a new track when the time gap exceeds this (default: 60)")
    ap.add_argument("--no-sort", action="store_true",
                    help="keep file/segment order instead of sorting points by time")
    ap.add_argument("--points-per-part", type=int, default=None,
                    help="also write part files with at most N points each")
    ap.add_argument("--overlap", type=int, default=0,
                    help="points repeated between consecutive part files")
    args = ap.parse_args()

    points, color, width, n_pm, n_single = read_points(args.input)
    if not points:
        sys.exit("No track points found in the input file.")
    print(f"Read   : {n_pm} placemarks -> {len(points)} points "
          f"({n_single} single-point fragments)")

    points = sort_points(points, args.no_sort)
    journeys = split_journeys(points, timedelta(minutes=args.gap_minutes))
    base = Path(args.input).stem
    out = Path(args.out) if args.out else Path(base + "_repaired.kml")

    body = ""
    for k, pts in enumerate(journeys, 1):
        t0 = next((p["t"] for p in pts if p["t"] is not None), None)
        t1 = next((p["t"] for p in reversed(pts) if p["t"] is not None), None)
        span = f"{t0.isoformat()} -> {t1.isoformat()}" if t0 else "no timestamps"
        print(f"Journey {k}: {len(pts):>6} points | {span}")
        body += journey_kml(f"{base} - Journey {k}", pts, color, width)
    out.write_text(kml_document(f"{base} (repaired)", body, color, width), encoding="utf-8")
    print(f"Wrote  : {out}  ({len(journeys)} track(s))")

    if args.points_per_part:
        if args.points_per_part < 2:
            ap.error("--points-per-part must be >= 2")
        if args.overlap < 0 or args.overlap >= args.points_per_part:
            ap.error("--overlap must be >= 0 and smaller than --points-per-part")
        out_dir = Path(out.stem + "_parts")
        out_dir.mkdir(parents=True, exist_ok=True)
        part_no = 0
        for k, pts in enumerate(journeys, 1):
            for i, j in chunk_ranges(len(pts), args.points_per_part, args.overlap):
                part_no += 1
                name = f"{base} - Journey {k} - Part {part_no:03d}"
                doc = kml_document(name, journey_kml(name, pts[i:j], color, width), color, width)
                (out_dir / f"{out.stem}_part{part_no:03d}.kml").write_text(doc, encoding="utf-8")
        print(f"Wrote  : {part_no} part file(s) to {out_dir}/")


if __name__ == "__main__":
    main()
