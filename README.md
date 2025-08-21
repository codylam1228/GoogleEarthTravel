# Google Location History to KML Converter

A Python script that converts Google Location History JSON files (exported from Google Takeout) to KML format for visualization in Google Earth, Google Maps, or other mapping applications.

## Features

- **Complete Data Processing**: Handles both activity data (movements like walking, driving) and visit data (places you've been)
- **Real Movement Tracks**: Creates actual path tracks using GPS data, waypoints, and transit routes (not just point-to-point lines)
- **Daily Organization**: Option to organize data by day with separate folders for each date
- **Flexible Filtering**: Filter by date range, accuracy threshold, or data type
- **Rich KML Output**: Generates well-formatted KML with meaningful placemark names, descriptions, and visual styles
- **Smart Track Types**: Automatically detects and uses the best available path data (GPS tracks, waypoints, or transit routes)
- **Error Handling**: Robust error handling for malformed data and edge cases
- **Command Line Interface**: Easy-to-use CLI with comprehensive options
- **Modular Design**: Clean, well-documented code that's easy to modify and extend

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)


## Usage

### Basic Usage

Convert your entire location history:
```bash
python location_history_to_kml.py location-history.json output.kml
```

### Advanced Usage

Filter by date range:
```bash
python location_history_to_kml.py location-history.json output.kml \
    --start-date 2024-01-01 --end-date 2024-12-31
```

Include only visits (exclude activities):
```bash
python location_history_to_kml.py location-history.json output.kml --no-activities
```

Include only activities (exclude visits):
```bash
python location_history_to_kml.py location-history.json output.kml --no-visits
```

Organize data by day:
```bash
python location_history_to_kml.py location-history.json output.kml --group-by-day
```

Exclude movement tracks (points only):
```bash
python location_history_to_kml.py location-history.json output.kml --no-tracks
```

Combine options for specific date range organized by day:
```bash
python location_history_to_kml.py location-history.json output.kml \
    --group-by-day --start-date 2024-01-01 --end-date 2024-01-31
```

### Command Line Options

```
positional arguments:
  input_file            Input Google Location History JSON file
  output_file           Output KML file

optional arguments:
  -h, --help                Show help message and exit
  --start-date START_DATE   Start date filter (YYYY-MM-DD)
  --end-date END_DATE       End date filter (YYYY-MM-DD)
  --min-accuracy            MIN_ACCURACY
                            Minimum accuracy threshold (meters)
  --no-activities           Exclude activity data
  --no-visits               Exclude visit data
  --no-tracks               Exclude movement tracks
  --group-by-day            Organize data by day (creates daily folders with activities and visits subfolders)
```

## Getting Your Google Location History

1. Go to [Google Takeout](https://takeout.google.com/)
2. Select "Location History (Timeline)"
3. Choose JSON format (not KML)
4. Download and extract the archive
5. Look for the `location-history.json` file

## Output Format

The generated KML file contains:

### Standard Organization (Default)
- **Activities Folder** (hidden by default): Start/end points for movements
- **Visits Folder** (hidden by default): Places you visited
- **Tracks Folder** (visible): Real movement paths with deep blue lines

### Daily Organization (--group-by-day)
- **Daily Folders** (e.g., "2024-01-01"): One folder per day containing:
  - **Activities Subfolder** (hidden): Start/end points for that day
  - **Visits Subfolder** (hidden): Places visited that day
  - **Tracks Subfolder** (visible): Movement paths for that day

### Data Types

#### Activities Folder
- **Start Points** (Green markers): Where activities began
- **End Points** (Red markers): Where activities ended
- **Information**: Activity type (walking, driving, etc.), distance, probability

#### Visits Folder
- **Visit Points** (Blue/Yellow markers): Places you visited
- **Information**: Place type, duration, probability, Google Place ID
- **Hierarchy Levels**: Different colors for different hierarchy levels

#### Tracks Folder
- **Movement Tracks** (Deep blue lines): Real paths taken during activities
- **Track Types**:
  - **GPS Track**: From actual GPS breadcrumbs (most accurate)
  - **Waypoint Track**: From route waypoints
  - **Transit Track**: From public transit stops
  - **Simple Track**: Fallback straight line between points
- **Information**: Activity type, track type, number of points, duration, distance

## Data Structure Understanding

The converter handles two main types of location data:

### Activities
Movement between locations with:
- Start and end coordinates
- Activity type (walking, in_passenger_vehicle, etc.)
- Distance and duration
- Confidence probability
- **Path data**: GPS tracks, waypoints, or transit routes for real movement visualization

### Visits
Time spent at specific locations with:
- Place coordinates
- Semantic type (home, work, restaurant, etc.)
- Duration of visit
- Google Place ID
- Confidence probability

### Tracks
Real movement paths extracted from Google's location data:
- **GPS Tracks**: Actual GPS breadcrumbs showing precise routes taken
- **Waypoint Tracks**: Key points along planned routes
- **Transit Tracks**: Public transportation stops and connections
- **Automatic Selection**: Uses the most accurate path data available for each activity
