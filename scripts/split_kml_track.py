"""
split_kml_track.py - Split a large KML track into smaller part files,
so each part can be imported into a map one by one.

Handles both plain LineString tracks (e.g. GPS-logger exports like
15-Aug-2026-0042.kml) and gx:Track tracks. Every part keeps the original
line style and, when the source description contains Start/End times,
each part gets its own interpolated Start/End and a TimeSpan.

Usage:
    uv run python split_kml_track.py big.kml                      # 2000 points per part (default)
    uv run python split_kml_track.py big.kml --points 5000
    uv run python split_kml_track.py big.kml --parts 20           # aim for ~20 part files
    uv run python split_kml_track.py big.kml --points 2000 --overlap 1 --out-dir parts

Output:
    <out-dir>/<name>_part001.kml, _part002.kml, ...  (numbering continues
    across all track segments found in the input)
"""

import argparse
import math
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from html import escape
from pathlib import Path

KML = "http://www.opengis.net/kml/2.2"
GX = "http://www.google.com/kml/ext/2.2"
NS = {"k": KML, "gx": GX}
ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")


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
    return start, end


def read_linestyle(root):
    color, width = "ff0000ff", "4"
    ls = root.find(f".//{{{KML}}}Style/{{{KML}}}LineStyle")
    if ls is not None:
        color = ls.findtext(f"{{{KML}}}color", default=color)
        width = ls.findtext(f"{{{KML}}}width", default=width)
    return color, width


def read_segments(path):
    """Return (segments, color, width). Coordinates are kept as raw strings
    to preserve full precision. Each segment: {name, coords[str], whens[datetime]|None,
    start, end}."""
    root = ET.parse(path).getroot()
    color, width = read_linestyle(root)
    segments = []
    for pm in root.iter(f"{{{KML}}}Placemark"):
        name = pm.findtext("k:name", default="track", namespaces=NS)
        desc = pm.findtext("k:description", default="", namespaces=NS)

        track = pm.find(".//gx:Track", NS)
        if track is not None:
            whens = [parse_dt(w.text) for w in track.findall("k:when", NS)]
            coords = [c.text.strip() for c in track.findall("gx:coord", NS)]
            n = min(len(whens), len(coords))
            if n >= 2:
                segments.append({"name": name, "coords": coords[:n], "whens": whens[:n],
                                 "start": whens[0], "end": whens[-1], "gx": True})
            continue

        coord_el = pm.find(".//k:LineString/k:coordinates", NS)
        if coord_el is None or not coord_el.text:
            continue
        coords = coord_el.text.split()
        if len(coords) < 2:
            continue
        start, end = desc_start_end(desc)
        segments.append({"name": name, "coords": coords, "whens": None,
                         "start": start, "end": end, "gx": False})
    return segments, color, width


def chunk_ranges(n, size, overlap):
    """Yield (start, end) index pairs. A small remainder is merged into the
    previous chunk instead of producing a tiny tail file."""
    step = size - overlap
    tail_merge = max(overlap, size // 10)
    i = 0
    while True:
        j = min(i + size, n)
        if n - j <= tail_merge:
            j = n
        yield i, j
        if j >= n:
            break
        i += step


def time_at(seg, idx):
    """Interpolated (or exact) timestamp of point idx, or None."""
    if seg["whens"] is not None:
        return seg["whens"][idx]
    if seg["start"] is None or seg["end"] is None:
        return None
    n = len(seg["coords"])
    return seg["start"] + (seg["end"] - seg["start"]) * (idx / (n - 1))


def write_part(path, seg, i, j, part_no, color, width):
    coords = seg["coords"][i:j]
    t0, t1 = time_at(seg, i), time_at(seg, j - 1)
    name = f'{seg["name"]} - Part {part_no:03d}'

    if seg["gx"]:
        whens = "".join(f"<when>{time_at(seg, k).isoformat()}</when>" for k in range(i, j))
        gxcoords = "".join(f"<gx:coord>{c}</gx:coord>" for c in coords)
        geom = f"<gx:Track>{whens}{gxcoords}</gx:Track>"
    else:
        geom = ("<LineString><altitudeMode>clampToGround</altitudeMode>"
                f"<coordinates>{' '.join(coords)}</coordinates></LineString>")

    desc = f"<b>Track points</b>: {len(coords)}"
    if t0 is not None and t1 is not None:
        desc += f"<br><b>Start</b>: {t0.isoformat()}<br><b>End</b>: {t1.isoformat()}"
    timespan = ""
    if t0 is not None and t1 is not None:
        timespan = f"<TimeSpan><begin>{t0.isoformat()}</begin><end>{t1.isoformat()}</end></TimeSpan>"

    kml = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<kml xmlns="{KML}" xmlns:gx="{GX}">\n<Document>\n'
           f'<name>{escape(name)}</name>\n'
           f'<Style id="track"><LineStyle><color>{color}</color>'
           f'<width>{width}</width></LineStyle></Style>\n'
           f'<Placemark><name>{escape(name)}</name>\n'
           f'<description>{escape(desc)}</description>\n'
           f'{timespan}<styleUrl>#track</styleUrl>\n'
           f'{geom}</Placemark>\n</Document>\n</kml>\n')
    Path(path).write_text(kml, encoding="utf-8")
    return len(coords), t0, t1


def main():
    ap = argparse.ArgumentParser(description="Split a large KML track into smaller part files.")
    ap.add_argument("input", help="input .kml file")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--points", type=int, default=2000,
                     help="max track points per part file (default: 2000)")
    grp.add_argument("--parts", type=int, default=None,
                     help="aim for roughly this many part files")
    ap.add_argument("--overlap", type=int, default=0,
                    help="points repeated between consecutive parts so the line "
                         "looks continuous when all parts are shown (e.g. 1)")
    ap.add_argument("--out-dir", default=None,
                    help="output folder (default: <input name>_parts)")
    args = ap.parse_args()

    segments, color, width = read_segments(args.input)
    if not segments:
        sys.exit("No track segments found in the KML file.")
    total = sum(len(s["coords"]) for s in segments)

    size = args.points
    if args.parts is not None:
        if args.parts < 1:
            ap.error("--parts must be >= 1")
        size = math.ceil(total / args.parts)
    if size < 2:
        ap.error("chunk size must be >= 2 points")
    if args.overlap < 0 or args.overlap >= size:
        ap.error("--overlap must be >= 0 and smaller than the chunk size")

    base = Path(args.input).stem
    out_dir = Path(args.out_dir) if args.out_dir else Path(base + "_parts")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Input  : {args.input} | {len(segments)} segment(s), {total} points total")
    print(f"Split  : max {size} points/part, overlap {args.overlap} -> {out_dir}/")
    part_no, files = 0, 0
    for seg in segments:
        for i, j in chunk_ranges(len(seg["coords"]), size, args.overlap):
            part_no += 1
            fname = out_dir / f"{base}_part{part_no:03d}.kml"
            npts, t0, t1 = write_part(fname, seg, i, j, part_no, color, width)
            span = f" | {t0.isoformat()} -> {t1.isoformat()}" if t0 else ""
            print(f"  part {part_no:03d}: {npts:>6} points{span}  ({fname.name})")
            files += 1
    print(f"Done   : {files} part file(s) written to {out_dir}/")
    print("Import them into your map one by one, in filename order.")


if __name__ == "__main__":
    main()