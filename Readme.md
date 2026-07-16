<!-- markdownlint-disable first-line-h1 -->
<!-- markdownlint-disable html -->
<!-- markdownlint-disable no-duplicate-header -->

<div align="center">
  <img src="https://i0.wp.com/techpressionmedia.com/wp-content/uploads/2024/02/Google-Earth-1.jpg" width="60%" alt="Google Earth" />
</div>

# Travel Track Recorder and Google Earth SOP

This project provides a simple local workflow for recording travel tracks with **Open GPX Tracker**, converting exported GPX files into KML files, and displaying the results in **Google Earth**.

The workflow does not require Google Maps Timeline, a cloud database, a continuously running server, or Docker. All track processing is performed locally on the computer.

```text
Open GPX Tracker
        ↓
Export GPX after a trip
        ↓
Place GPX in input/
        ↓
Run the Python conversion script with uv
        ↓
Get KML in output/
        ↓
Import KML into Google Earth
```

## Prerequisites

Before using this workflow, prepare the following:

- An iPhone or Apple Watch with [Open GPX Tracker](https://apps.apple.com/us/app/open-gpx-tracker/id984503772)
- A computer with Python and [uv](https://docs.astral.sh/uv/)
- Google Earth or Google Earth Pro
- This project repository, including `convert.py`

Google Earth supports opening and importing KML files. See the official [Google Earth KML import guide](https://support.google.com/earth/answer/7365595?hl=en) for more information.

## Project Structure

The project folder should have the following structure:

```text
GoogleEarthTravel/
├── input/          # Add newly exported GPX files here
├── output/         # Generated KML files are saved here
├── archive/        # Successfully processed GPX files are moved here
├── convert.py      # GPX-to-KML conversion script
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

Install the Python dependencies once from the project root directory:

```bash
uv sync
```

If the project has not been configured yet, install the required packages:

```bash
uv add gpxpy simplekml
```

## SOP: Record a Travel Track

### Step 1: Create a New Track

1. Open **Open GPX Tracker** on the iPhone or Apple Watch.
2. Create a new track.
3. Give the track a name, such as:

```text
2026-07-16_Tokyo_Asakusa-Shibuya
```

4. Press **Record** or **Start** before beginning the journey.

### Step 2: Add Important Waypoints

During the journey, add a waypoint whenever you reach an important location.

Examples include:

- Hotel
- Airport
- Train station
- Restaurant
- Tourist attraction
- Hiking checkpoint
- Meeting point


Each waypoint will be exported to the GPX file and displayed as a point in Google Earth.

### Step 3: Stop and Save the Track

At the end of the journey:

1. Stop the recording.
2. Save the track.
3. Review the track and waypoints if necessary.
4. Export the saved track as a GPX file.

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

## SOP: Export GPX from Open GPX Tracker

1. Open the completed track in Open GPX Tracker.
2. Select the **Share** or **Export** action.
3. Choose the **GPX** format.
4. Transfer the file to the computer using one of the following methods:
   - AirDrop
   - iCloud Drive
   - Files app
   - Email
   - USB file transfer
5. Copy the exported `.gpx` file into the project `input/` folder.

Example:

```text
travel-track-project/
└── input/
    └── 2026-07-16_Tokyo_Asakusa-Shibuya.gpx
```

## SOP: Convert GPX to KML

From the project root directory, run:

```bash
uv run python convert.py
```

The script will automatically:

1. Find all `.gpx` files in `input/`
2. Convert each GPX file into an individual KML file
3. Save generated KML files in `output/`
4. Move successfully processed GPX files to `archive/`
5. Keep failed GPX files in `input/` for troubleshooting

Example result:

```text
travel-track-project/
├── input/
├── output/
│   └── 2026-07-16_Tokyo_Asakusa-Shibuya.kml
└── archive/
    └── 2026-07-16_Tokyo_Asakusa-Shibuya_20260716_223000.gpx
```

## SOP: Import KML into Google Earth

### Google Earth Web

1. Open [Google Earth](https://earth.google.com/web/).
2. Create a new project, or open an existing project.
3. Select **New feature** or **Import file**.
4. Select the generated KML file from the `output/` folder.
5. Wait for the file to load.
6. Save the Google Earth project if required.

### Google Earth Pro

1. Open Google Earth Pro.
2. Select **File** → **Open**.
3. Select the generated `.kml` file in the `output/` folder.
4. The track and waypoints will appear in the left-side **Places** panel.
5. Drag the KML file into **My Places** if you want to keep it available after restarting Google Earth Pro.

## KML Display Structure

Each generated KML file contains separate folders for tracks and waypoints:

```text
Trip Name
├── Tracks
│   └── Track 1
└── Waypoints
    ├── Hotel Check-in
    ├── Tokyo Station
    ├── Lunch - Sushi Restaurant
    └── Senso-ji Temple
```

This allows tracks and waypoints to be shown or hidden separately in Google Earth.

## Notes

- Start recording only when the journey begins to reduce unnecessary GPS points and battery usage.
- Stop recording immediately after the journey ends.
- GPS accuracy may be reduced indoors, underground, in tunnels, or near dense high-rise buildings.
- Use waypoints to mark important places instead of relying only on the track line.
- Keep one GPX file per day or per travel activity for easier management.
- Keep the original GPX files in `archive/` as the source data.
- The generated KML files can also be opened by other GIS tools that support KML, such as QGIS.

## What We Used

- [Open GPX Tracker](https://apps.apple.com/us/app/open-gpx-tracker/id984503772)
- [uv](https://docs.astral.sh/uv/)
- Python
- Google Earth
- KML
- GPX