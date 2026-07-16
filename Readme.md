<!-- markdownlint-disable first-line-h1 -->
<!-- markdownlint-disable html -->
<!-- markdownlint-disable no-duplicate-header -->

<div align="center">
  <img src="https://i0.wp.com/techpressionmedia.com/wp-content/uploads/2024/02/Google-Earth-1.jpg" width="60%" alt="Google Earth" />
</div>

# Travel Track Recorder and Google Earth SOP

This project provides a local workflow for converting travel-location data into KML files for viewing in Google Earth.

It supports two input sources:

- **GPX files** exported from Open GPX Tracker on iPhone or Apple Watch
- **JSON files** exported from Google Maps Timeline

The workflow does not require a cloud database, a continuously running server, Docker, or a third-party online conversion service. All conversion is performed locally on the computer.

```text
Open GPX Tracker / Google Maps Timeline
                ↓
Export GPX or JSON file
                ↓
Place file in input/
                ↓
Run convert.py with uv
                ↓
KML file created in output/
                ↓
Import KML into Google Earth
```

## Supported Input Formats

| Input format | Source | KML output |
|---|---|---|
| `.gpx` | Open GPX Tracker | GPS track lines and manually added waypoints |
| `.json` | Google Maps Timeline export | Activity start/end lines and visit location markers |

> [!NOTE]
> GPX files contain detailed GPS trackpoints, so their KML output represents the actual recorded travel path.
>
> The supported Google Maps Timeline JSON format only contains activity start and end coordinates. Therefore, each activity is displayed as a straight line, not the actual road, railway, or walking route.

## Prerequisites

Prepare the following before using this project:

- An iPhone or Apple Watch with [Open GPX Tracker](https://apps.apple.com/us/app/open-gpx-tracker/id984503772), if recording new travel tracks
- A computer with [uv](https://docs.astral.sh/uv/) installed
- Google Earth Web or Google Earth Pro
- This project repository, including `convert.py`

Google Earth supports local KML files and can import KML/KMZ data into a Google Earth project.

## Project Structure

The project directory must use the following structure:

```text
GoogleEarthTravel/
├── input/          # Add GPX or Google Timeline JSON files here
├── output/         # Generated KML files are saved here
├── archive/        # Successfully processed source files are moved here
├── convert.py      # GPX/JSON-to-KML conversion script
├── pyproject.toml
└── uv.lock
```

Create the required folders if they do not already exist.

### macOS / Linux

```bash
mkdir -p input output archive
```

### Windows PowerShell

```powershell
mkdir input, output, archive
```

## Initial Setup

Install the project dependencies once from the project root directory:

```bash
uv sync
```

If `pyproject.toml` does not yet contain the dependencies, run:

```bash
uv add gpxpy simplekml
```

## SOP: Record a Travel Track

This section applies to new trips recorded with Open GPX Tracker.

### Step 1: Create a Track

1. Open **Open GPX Tracker** on an iPhone or Apple Watch.
2. Create a new track.
3. Give the track a meaningful name.

Example:

```text
2026-07-16_Tokyo_Asakusa-Shibuya
```

4. Press **Record** or **Start** before beginning the journey.

### Step 2: Add Waypoints

During the journey, add a waypoint whenever you arrive at an important location.

Suggested waypoint types:

- Hotel
- Airport
- Train station
- Restaurant
- Tourist attraction
- Hiking checkpoint
- Meeting point

Recommended waypoint names:

```text
Hotel Check-in
Tokyo Station
Lunch - Sushi Restaurant
Senso-ji Temple
Shibuya Crossing
```

Waypoints are exported with the GPX file and displayed as location markers in Google Earth.

### Step 3: Stop and Save

At the end of the journey:

1. Stop the recording.
2. Save the track.
3. Review the track and waypoints if necessary.
4. Export the completed track as a GPX file.

Recommended filename format:

```text
YYYY-MM-DD_City_TripName.gpx
```

Examples:

```text
2026-07-16_Tokyo_Asakusa-Shibuya.gpx
2026-07-17_Tokyo_Kamakura-DayTrip.gpx
2026-07-18_Okinawa_Naha-Walk.gpx
```

## SOP: Export GPX

1. Open the completed track in Open GPX Tracker.
2. Select **Share** or **Export**.
3. Choose the **GPX** format.
4. Transfer the file to the computer using AirDrop, iCloud Drive, Files, email, or USB transfer.
5. Copy the exported `.gpx` file into the project `input/` folder.

Example:

```text
GoogleEarthTravel/
└── input/
    └── 2026-07-16_Tokyo_Asakusa-Shibuya.gpx
```

## SOP: Export Google Timeline JSON

This section is for importing historical location data from Google Maps Timeline.

1. Open Google Maps Timeline settings on the mobile device.
2. Export the Timeline data as a JSON file.
3. Transfer the exported JSON file to the computer.
4. Copy the `.json` file into the project `input/` folder.

Example:

```text
GoogleEarthTravel/
└── input/
    └── location-history.json
```

The currently supported Google Timeline JSON structure is a top-level JSON array containing records such as:

```json
[
  {
    "startTime": "2025-12-21T20:49:49.103+08:00",
    "endTime": "2025-12-21T20:54:50.103+08:00",
    "activity": {
      "start": "geo:22.339023,114.202798",
      "end": "geo:22.334279,114.195603",
      "distanceMeters": "908.833374",
      "topCandidate": {
        "type": "in passenger vehicle",
        "probability": "0.547723"
      }
    }
  }
]
```

> [!WARNING]
> Do not modify, truncate, or manually copy only part of the exported JSON file.
>
> The source file must be complete valid JSON, beginning with `[` and ending with `]`.

## SOP: Convert GPX or JSON to KML

Place one or more supported files in `input/`.

Example:

```text
GoogleEarthTravel/
├── input/
│   ├── 2026-07-16_Tokyo_Asakusa-Shibuya.gpx
│   └── location-history.json
├── output/
├── archive/
└── convert.py
```

Run the converter from the project root directory:

```bash
uv run python convert.py
```

The script will automatically:

1. Find all `.gpx` and `.json` files in `input/`
2. Detect each file type automatically
3. Convert each supported file into an individual KML file
4. Save generated KML files in `output/`
5. Move successfully processed source files to `archive/`
6. Keep failed source files in `input/` for troubleshooting

Example terminal output:

```text
Found 2 supported file(s).
------------------------------------------------------------
SUCCESS: 2026-07-16_Tokyo_Asakusa-Shibuya.gpx
  Type:    GPX
  GPX segments converted: 1
  GPX waypoints converted: 6
  KML:     output\2026-07-16_Tokyo_Asakusa-Shibuya.kml
  Archive: archive\2026-07-16_Tokyo_Asakusa-Shibuya_20260716_220000.gpx
------------------------------------------------------------
SUCCESS: location-history.json
  Type:    JSON
  Timeline activities converted: 125
  Timeline visits converted: 92
  Timeline records skipped: 0
  KML:     output\location-history.kml
  Archive: archive\location-history_20260716_220000.json
------------------------------------------------------------
Finished. Success: 2, Failed: 0
```

## Output and Archive

After successful conversion, the directory structure will look similar to this:

```text
GoogleEarthTravel/
├── input/
├── output/
│   ├── 2026-07-16_Tokyo_Asakusa-Shibuya.kml
│   └── location-history.kml
├── archive/
│   ├── 2026-07-16_Tokyo_Asakusa-Shibuya_20260716_220000.gpx
│   └── location-history_20260716_220000.json
├── convert.py
├── pyproject.toml
└── uv.lock
```

Source files are moved to `archive/` only after a valid non-empty KML file has been created.

If conversion fails, the source file remains in `input/`.

## SOP: Import KML into Google Earth

### Google Earth Web

1. Open [Google Earth](https://earth.google.com/web/).
2. Create a new project or open an existing project.
3. Select **New feature** or **Import file**.
4. Select a `.kml` file from the `output/` folder.
5. Wait for the file to load.
6. Save the Google Earth project if required.

### Google Earth Pro

1. Open Google Earth Pro.
2. Select **File** → **Open**.
3. Select a `.kml` file from the `output/` folder.
4. The KML content appears in the left-side **Places** panel.
5. Drag the imported item into **My Places** to keep it after restarting Google Earth Pro.

## KML Structure: GPX Files

KML files generated from GPX contain separate folders for recorded travel tracks and manually added waypoints.

```text
2026-07-16_Tokyo_Asakusa-Shibuya
├── Tracks
│   └── Track 1
└── Waypoints
    ├── Hotel Check-in
    ├── Tokyo Station
    ├── Lunch - Sushi Restaurant
    └── Senso-ji Temple
```

This lets you show or hide route lines and waypoint markers independently.

## KML Structure: Timeline JSON

KML files generated from Google Timeline JSON contain separate folders for activities and visits.

```text
location-history
├── Activities (straight lines)
│   ├── Activity 1: in passenger vehicle
│   ├── Activity 3: in subway
│   └── Activity 5: walking
└── Visits
    ├── Visit 2: Unknown
    ├── Visit 4: Unknown
    └── Visit 6: Unknown
```

### Activity Output

Each Timeline activity contains:

- Start time and end time
- Activity type, such as `in passenger vehicle` or `in subway`
- Google confidence score
- Distance estimate
- A line between the provided start and end coordinates

### Visit Output

Each Timeline visit contains:

- Arrival and departure time
- Duration
- Semantic type, if available
- Google Place ID, if available
- Google confidence score
- A location marker

## Important Notes

- Start GPX recording only when the journey begins to reduce unnecessary GPS points and battery usage.
- Stop recording immediately after the journey ends.
- GPS accuracy may be reduced indoors, underground, in tunnels, or near dense high-rise buildings.
- Use waypoints to mark important places during GPX recording.
- Keep one GPX file per day or per travel activity for easier management.
- Keep original GPX and JSON files in `archive/` as source data.
- The script processes only files directly inside `input/`; it does not scan subfolders.
- The script supports `.gpx`, `.GPX`, `.json`, and `.JSON` filenames.
- GPX output shows detailed routes because GPX contains trackpoints.
- Google Timeline JSON output may show straight lines because the exported activity records may contain only start and end coordinates.
- Generated KML files can also be opened using GIS tools that support KML, such as QGIS.

## Troubleshooting

### No files are found

Check that the source files are located directly inside:

```text
GoogleEarthTravel/input/
```

Supported extensions are:

```text
.gpx
.GPX
.json
.JSON
```

### A file is processed twice

Use the latest version of `convert.py`.

The script scans the `input/` folder once and checks extensions with case-insensitive matching, preventing Windows from treating `.gpx` and `.GPX` as separate file matches.

### JSON conversion fails

Check that the JSON file is complete and valid.

A valid Timeline JSON export should:

- Begin with `[`
- End with `]`
- Contain complete JSON objects
- Use `activity` and/or `visit` records
- Include `geo:latitude,longitude` coordinate values

### Google Earth shows a straight line

This is expected for some Google Maps Timeline JSON exports.

The file may contain only the start coordinate and end coordinate of an activity, rather than all intermediate GPS trackpoints. Use Open GPX Tracker for future trips when detailed route geometry is required.

## Technologies Used

- [Open GPX Tracker](https://apps.apple.com/us/app/open-gpx-tracker/id984503772)
- [uv](https://docs.astral.sh/uv/)
    - Python
        - [gpxpy](https://github.com/tkrajina/gpxpy)
        - [simplekml](https://simplekml.readthedocs.io/)
- Google Maps Timeline
- Google Earth