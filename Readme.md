<!-- markdownlint-disable first-line-h1 -->
<!-- markdownlint-disable html -->
<!-- markdownlint-disable no-duplicate-header -->

<div align="center">
  <img src="https://i0.wp.com/techpressionmedia.com/wp-content/uploads/2024/02/Google-Earth-1.jpg" width="60%" alt="Google Earth" />
</div>

# Travel Track Recorder and Google Earth SOP

This project provides a local and web-based workflow for converting, repairing, pruning, and splitting travel track data into KML files for viewing in Google Earth.

It supports:
- **GPX files** exported from Open GPX Tracker
- **JSON files** exported from Google Maps Timeline
- **KML processing utilities**: Pruning by date, repairing fragmented track segments, and splitting large tracks.

---

## 🌐 Web Application (Pyodide WASM)

You can run all operations inside your browser without installing Python:
👉 **[Open Web Suite](https://codylam1228.github.io/GoogleEarthTravel/)**

Features:
- **100% Client-Side**: All conversions run locally using Pyodide (Python WebAssembly). No data is sent to external servers.
- **Bilingual Interface**: Toggle between English and Traditional Chinese (繁體中文).

---

## 🐍 CLI Scripts & Utilities

| Script | Purpose |
|---|---|
| `convert.py` / `converter.py` | Batch converts GPX or Google Timeline JSON files in `input/` into KML files. |
| `prune_kml_by_date.py` | Filters out Placemarks/Tracks that do not match a target date. |
| `repair_kml_track.py` | Merges fragmented GPS points/segments into unified, time-ordered tracks. |
| `split_kml_track.py` | Splits large KML files into smaller parts for smoother import. |
