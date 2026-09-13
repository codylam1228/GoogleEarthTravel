"""
prune_kml_by_date.py
--------------------
Remove every Placemark (LineString track, Point waypoint, gx:Track, etc.)
from a KML file that does NOT fall on the user-supplied date.

A placemark is kept if ANY of its timestamps (or its Start/End range in the
<description>) touches the target date. Placemarks with no date information
are KEPT by default (with a warning) so data is never deleted silently —
use --drop-undated to remove them too.

Usage:
    python prune_kml_by_date.py input.kml 08-Aug-2026
    python prune_kml_by_date.py input.kml 08-Aug-2026 -o out.kml --utc-offset 8
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

KML = "http://www.opengis.net/kml/2.2"
GX = "http://www.google.com/kml/ext/2.2"
ET.register_namespace("", KML)
ET.register_namespace("gx", GX)

def kml(t): return f"{{{KML}}}{t}"
def gx(t):  return f"{{{GX}}}{t}"

ISO_RE = re.compile(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(?:\s*(Z|[+-]\d{2}:?\d{2}))?")
NAME_DATE_RE = re.compile(r"(\d{1,2}-[A-Za-z]{3}-\d{4})")


def parse_target(s):
    try:
        return datetime.strptime(s, "%d-%b-%Y").date()
    except ValueError:
        sys.exit(f"Error: cannot parse date '{s}'. Expected format like 08-Aug-2026")


def to_utc(d, t, off):
    """Parse ISO date/time + optional offset -> naive datetime in UTC."""
    dt = datetime.fromisoformat(f"{d}T{t}")
    if off and off != "Z":
        off = off if ":" in off else f"{off[:3]}:{off[3:]}"
        sign = 1 if off[0] == "+" else -1
        dt -= sign * timedelta(hours=int(off[1:3]), minutes=int(off[4:6]))
    return dt


def datetimes_in(text):
    """Extract all ISO datetimes from a text blob, as naive UTC datetimes."""
    if not text:
        return []
    out = []
    for m in ISO_RE.finditer(text):
        try:
            out.append(to_utc(m.group(1), m.group(2), m.group(3)))
        except ValueError:
            pass
    return out


def local_date(dt_utc, offset):
    return (dt_utc + offset).date()


def placemark_dates(pm, offset):
    """
    Return the set of local calendar dates this placemark touches,
    or None if no date information is found anywhere.
    """
    dts = []
    # 1) <when> (TimeStamp / gx:Track) and <begin>/<end> (TimeSpan)
    for el in pm.iter():
        if el.tag in (kml("when"), kml("begin"), kml("end")):
            dts += datetimes_in(el.text)
    # 2) <description>  (e.g. "Start: 2026-08-14T07:19:49+00:00<br>End: ...")
    desc = pm.find(kml("description"))
    if desc is not None:
        dts += datetimes_in(desc.text)

    dates = set()
    if dts:
        lo, hi = min(dts) + offset, max(dts) + offset
        d = lo.date()
        while d <= hi.date():          # every calendar day the range spans
            dates.add(d)
            d += timedelta(days=1)
    else:
        # 3) fallback: date written in the <name>, e.g. "15-Aug-2026-0042 - Track 1"
        name = pm.find(kml("name"))
        if name is not None and name.text:
            m = NAME_DATE_RE.search(name.text)
            if m:
                try:
                    dates.add(datetime.strptime(m.group(1), "%d-%b-%Y").date())
                except ValueError:
                    pass
    return dates or None


def trim_gx_track(pm, target, offset):
    """
    Per-point trimming for <gx:Track>: drop <when>/<gx:coord> pairs not on
    the target date. Returns number of points remaining (None if no gx:Track).
    """
    track = pm.find(gx("Track"))
    if track is None:
        return None
    whens  = track.findall(kml("when"))
    coords = track.findall(gx("coord"))
    for w, c in zip(whens, coords):
        dt = datetimes_in(w.text)
        keep = dt and local_date(dt[0], offset) == target
        if not keep:
            track.remove(w)
            track.remove(c)
    return len(track.findall(gx("coord")))


def main():
    ap = argparse.ArgumentParser(description="Prune KML placemarks not on a given date.")
    ap.add_argument("input", help="input KML file")
    ap.add_argument("date", help="target date, e.g. 08-Aug-2026")
    ap.add_argument("-o", "--output", help="output KML file (default: <input>_pruned.kml)")
    ap.add_argument("--utc-offset", type=float, default=8.0,
                    help="local timezone offset in hours used to decide the date (default: +8, HKT)")
    ap.add_argument("--drop-undated", action="store_true",
                    help="also remove placemarks that carry no date information")
    args = ap.parse_args()

    target = parse_target(args.date)
    offset = timedelta(hours=args.utc_offset)
    output = args.output or re.sub(r"\.kml$", "", args.input, flags=re.I) + "_pruned.kml"

    tree = ET.parse(args.input)
    root = tree.getroot()
    parent = {c: p for p in root.iter() for c in p}   # child -> parent map

    kept = removed = undated = 0
    for pm in list(root.iter(kml("Placemark"))):
        name_el = pm.find(kml("name"))
        name = name_el.text if name_el is not None else "(unnamed)"

        remaining = trim_gx_track(pm, target, offset)
        if remaining is not None:                    # gx:Track: per-point pruning
            if remaining > 0:
                kept += 1
                continue
        else:
            dates = placemark_dates(pm, offset)
            if dates is not None and target in dates:
                kept += 1
                continue
            if dates is None and not args.drop_undated:
                undated += 1
                print(f"  warning: kept '{name}' (no date information found)")
                continue

        parent[pm].remove(pm)
        removed += 1
        print(f"  removed: {name}")

    tree.write(output, xml_declaration=True, encoding="UTF-8")
    print(f"\nTarget date : {target} (UTC{args.utc_offset:+g})")
    print(f"Kept {kept}, removed {removed}, undated-but-kept {undated}")
    print(f"Written to  : {output}")


if __name__ == "__main__":
    main()