from __future__ import division
import json
from datetime import datetime

def _parse_timestamp(timestamp_str):
    """Parses a simplified subset of ISO 8601 timestamps. Handles YYYY-MM-DDTHH:MM:SSZ format only."""
    try:
        return datetime.fromisoformat(timestamp_str[:-6])  # Remove the timezone info for parsing
    except ValueError:
        return None  # Or raise a more informative exception

def _get_timestampms(start_time, end_time):
    # Use startTime as the main timestamp for each entry
    parsed_time = _parse_timestamp(start_time)
    if parsed_time:
        return str(int(parsed_time.timestamp() * 1000))
    else:
        return None  # Handle parsing error appropriately

def _write_header(output, format, js_variable, separator):
    if format == "kml":
        output.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        output.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n")
        output.write("  <Document>\n")
        output.write("    <name>Location History</name>\n")

def _write_location(output, format, coordinates, timestamp):
    if format == "kml":
        output.write("    <Placemark>\n")
        output.write("      <TimeStamp><when>")
        time = datetime.utcfromtimestamp(int(timestamp) / 1000)
        output.write(time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        output.write("</when></TimeStamp>\n")
        output.write(
            "      <Point><coordinates>%s,%s</coordinates></Point>\n" %
            (coordinates[1], coordinates[0])  # longitude, latitude
        )
        output.write("    </Placemark>\n")

def _write_footer(output, format):
    if format == "kml":
        output.write("  </Document>\n</kml>\n")

def convert(locations, output, format="kml"):
    _write_header(output, format, "locationJsonData", ",")

    for item in locations:
        if "activity" in item:
            start_geo = item["activity"]["start"]
            end_geo = item["activity"]["end"]
            
            # Extract latitude and longitude from the geo strings
            start_coords = list(map(float, start_geo[4:].split(',')))  # Remove "geo:" and split
            end_coords = list(map(float, end_geo[4:].split(',')))  # Remove "geo:" and split
            
            # Get timestamps
            timestamp = _get_timestampms(item["startTime"], item["endTime"])
            if timestamp:
                _write_location(output, format, start_coords, timestamp)

    _write_footer(output, format)

if __name__ == "__main__":
    # Path to the JSON file
    json_file_path = "xxx/xxx/xxx/abc.json"

    # Load location data from JSON file
    with open(json_file_path, "r") as json_file:
        sample_locations = json.load(json_file)

    print("Loaded locations:", sample_locations)  # Print loaded locations

    # Convert to KML format
    with open("output.kml", "w") as output_file:
        convert(sample_locations, output_file, format="kml")

    print("Conversion complete. Output saved to output.kml.")