#!/usr/bin/env python3
"""
Google Location History to KML Converter

This script converts Google Location History JSON files (from Google Takeout)
to KML format for visualization in Google Earth or other mapping applications.

Author: codylam
Date: 2025-08-21
"""

import json
import argparse
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class LocationHistoryConverter:
    """Converts Google Location History JSON to KML format."""
    
    def __init__(self):
        self.activities = []
        self.visits = []
        self.tracks = []
        self.activities_by_day = defaultdict(list)
        self.visits_by_day = defaultdict(list)
        self.tracks_by_day = defaultdict(list)
        self.stats = {
            'total_entries': 0,
            'activities': 0,
            'visits': 0,
            'tracks': 0,
            'filtered_out': 0
        }
    
    def parse_geo_coordinate(self, geo_string: str) -> Optional[Tuple[float, float]]:
        """
        Parse geo coordinate string like 'geo:22.335799,114.173673'
        Returns (latitude, longitude) tuple or None if invalid.
        """
        if not geo_string or not geo_string.startswith('geo:'):
            return None
        
        try:
            coords = geo_string[4:].split(',')
            if len(coords) != 2:
                return None
            lat, lon = float(coords[0]), float(coords[1])
            return (lat, lon)
        except (ValueError, IndexError):
            return None
    
    def parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse ISO timestamp string to datetime object.
        Handles various formats including timezone info.
        """
        if not timestamp_str:
            return None
        
        try:
            # Handle different timestamp formats
            if timestamp_str.endswith('Z'):
                return datetime.fromisoformat(timestamp_str[:-1] + '+00:00')
            elif '+' in timestamp_str or timestamp_str.count('-') > 2:
                return datetime.fromisoformat(timestamp_str)
            else:
                return datetime.fromisoformat(timestamp_str)
        except ValueError:
            return None
    
    def format_timestamp_for_kml(self, dt: datetime) -> str:
        """Format datetime for KML display."""
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    def get_date_key(self, dt: datetime) -> str:
        """Get date key for grouping (YYYY-MM-DD format)."""
        return dt.strftime('%Y-%m-%d')

    def create_track_from_activity(self, activity: Dict) -> Optional[Dict]:
        """Create a track segment from activity data using real path information."""
        coordinates = []

        # Priority 1: Use simplifiedRawPath for most accurate GPS tracking
        if activity.get('simplified_raw_path') and activity['simplified_raw_path'].get('points'):
            points = activity['simplified_raw_path']['points']
            for point in points:
                # Convert from E7 format (degrees * 10^7) to regular degrees
                lat = point.get('latE7', 0) / 10000000.0
                lon = point.get('lngE7', 0) / 10000000.0
                if lat != 0 and lon != 0:  # Skip invalid coordinates
                    coordinates.append((lat, lon))

        # Priority 2: Use waypointPath for route waypoints
        elif activity.get('waypoint_path') and activity['waypoint_path'].get('waypoints'):
            waypoints = activity['waypoint_path']['waypoints']
            for waypoint in waypoints:
                # Convert from E7 format
                lat = waypoint.get('latE7', 0) / 10000000.0
                lon = waypoint.get('lngE7', 0) / 10000000.0
                if lat != 0 and lon != 0:
                    coordinates.append((lat, lon))

        # Priority 3: Use transit stops for public transport
        elif activity.get('transit_path') and activity['transit_path'].get('transitStops'):
            stops = activity['transit_path']['transitStops']
            for stop in stops:
                # Convert from E7 format
                lat = stop.get('latitudeE7', 0) / 10000000.0
                lon = stop.get('longitudeE7', 0) / 10000000.0
                if lat != 0 and lon != 0:
                    coordinates.append((lat, lon))

        # Fallback: Use start and end coordinates only
        elif activity.get('start_coords') and activity.get('end_coords'):
            coordinates = [activity['start_coords'], activity['end_coords']]

        # Need at least 2 points to create a track
        if len(coordinates) < 2:
            return None

        return {
            'coordinates': coordinates,
            'start_time': activity['start_time'],
            'end_time': activity['end_time'],
            'activity_type': activity['activity_type'],
            'distance': activity.get('distance'),
            'track_type': self.get_track_type(activity)
        }

    def get_track_type(self, activity: Dict) -> str:
        """Determine the type of track based on available path data."""
        if activity.get('simplified_raw_path'):
            return 'gps_track'
        elif activity.get('waypoint_path'):
            return 'waypoint_track'
        elif activity.get('transit_path'):
            return 'transit_track'
        else:
            return 'simple_track'
    
    def load_json_data(self, file_path: str) -> List[Dict]:
        """Load and parse JSON data from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("JSON data should be a list of location entries")
            
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def filter_by_date_range(self, entry: Dict, start_date: Optional[datetime],
                           end_date: Optional[datetime]) -> bool:
        """Check if entry falls within specified date range."""
        if not start_date and not end_date:
            return True

        entry_time = None
        if 'startTime' in entry:
            entry_time = self.parse_timestamp(entry['startTime'])
        elif 'endTime' in entry:
            entry_time = self.parse_timestamp(entry['endTime'])

        if not entry_time:
            return True  # Include entries with unparseable dates

        # Make sure we're comparing timezone-aware datetimes
        if start_date and start_date.tzinfo is None and entry_time.tzinfo is not None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date and end_date.tzinfo is None and entry_time.tzinfo is not None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        # Convert entry_time to naive if comparing with naive dates
        if start_date and start_date.tzinfo is None and entry_time.tzinfo is not None:
            entry_time = entry_time.replace(tzinfo=None)
        if end_date and end_date.tzinfo is None and entry_time.tzinfo is not None:
            entry_time = entry_time.replace(tzinfo=None)

        if start_date and entry_time < start_date:
            return False
        if end_date and entry_time > end_date:
            return False

        return True
    
    def filter_by_accuracy(self, entry: Dict, min_accuracy: Optional[float]) -> bool:
        """Filter entries based on accuracy threshold (if available)."""
        if not min_accuracy:
            return True
        
        # Note: Google Location History doesn't always include accuracy info
        # This is a placeholder for potential future accuracy filtering
        return True
    
    def process_activity(self, entry: Dict) -> Optional[Dict]:
        """Process an activity entry and extract relevant information."""
        activity = entry.get('activity', {})

        start_time = self.parse_timestamp(entry.get('startTime'))
        end_time = self.parse_timestamp(entry.get('endTime'))

        start_coords = self.parse_geo_coordinate(activity.get('start'))
        end_coords = self.parse_geo_coordinate(activity.get('end'))

        activity_type = activity.get('topCandidate', {}).get('type', 'Unknown')
        probability = float(activity.get('probability', 0))
        distance = activity.get('distanceMeters')

        # Extract path information for real tracks
        simplified_raw_path = activity.get('simplifiedRawPath')
        waypoint_path = activity.get('waypointPath')
        transit_path = activity.get('transitPath')

        if not start_coords and not end_coords:
            return None

        return {
            'type': 'activity',
            'activity_type': activity_type,
            'start_time': start_time,
            'end_time': end_time,
            'start_coords': start_coords,
            'end_coords': end_coords,
            'probability': probability,
            'distance': distance,
            'simplified_raw_path': simplified_raw_path,
            'waypoint_path': waypoint_path,
            'transit_path': transit_path
        }
    
    def process_visit(self, entry: Dict) -> Optional[Dict]:
        """Process a visit entry and extract relevant information."""
        visit = entry.get('visit', {})
        
        start_time = self.parse_timestamp(entry.get('startTime'))
        end_time = self.parse_timestamp(entry.get('endTime'))
        
        top_candidate = visit.get('topCandidate', {})
        location_coords = self.parse_geo_coordinate(top_candidate.get('placeLocation'))
        
        if not location_coords:
            return None
        
        place_id = top_candidate.get('placeID')
        semantic_type = top_candidate.get('semanticType', 'Unknown')
        probability = float(visit.get('probability', 0))
        hierarchy_level = visit.get('hierarchyLevel', '0')
        
        return {
            'type': 'visit',
            'start_time': start_time,
            'end_time': end_time,
            'coords': location_coords,
            'place_id': place_id,
            'semantic_type': semantic_type,
            'probability': probability,
            'hierarchy_level': hierarchy_level
        }
    
    def convert_to_kml(self, json_file: str, output_file: str,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      min_accuracy: Optional[float] = None,
                      include_activities: bool = True,
                      include_visits: bool = True,
                      group_by_day: bool = False,
                      include_tracks: bool = True) -> None:
        """
        Convert Google Location History JSON to KML format.

        Args:
            json_file: Path to input JSON file
            output_file: Path to output KML file
            start_date: Optional start date filter
            end_date: Optional end date filter
            min_accuracy: Optional minimum accuracy threshold
            include_activities: Whether to include activity data
            include_visits: Whether to include visit data
            group_by_day: Whether to organize data by day
            include_tracks: Whether to include movement tracks
        """
        print(f"Loading JSON data from {json_file}...")
        data = self.load_json_data(json_file)
        
        print(f"Processing {len(data)} entries...")
        
        for entry in data:
            self.stats['total_entries'] += 1
            
            # Apply filters
            if not self.filter_by_date_range(entry, start_date, end_date):
                self.stats['filtered_out'] += 1
                continue
            
            if not self.filter_by_accuracy(entry, min_accuracy):
                self.stats['filtered_out'] += 1
                continue
            
            # Process different entry types
            if 'activity' in entry and include_activities:
                processed = self.process_activity(entry)
                if processed:
                    self.activities.append(processed)
                    self.stats['activities'] += 1

                    # Create track segments for activities with path data
                    if include_tracks:
                        track_segment = self.create_track_from_activity(processed)
                        if track_segment:
                            self.tracks.append(track_segment)
                            self.stats['tracks'] += 1

                            if group_by_day and processed['start_time']:
                                date_key = self.get_date_key(processed['start_time'])
                                self.tracks_by_day[date_key].append(track_segment)

                    # Group by day if requested
                    if group_by_day and processed['start_time']:
                        date_key = self.get_date_key(processed['start_time'])
                        self.activities_by_day[date_key].append(processed)

            elif 'visit' in entry and include_visits:
                processed = self.process_visit(entry)
                if processed:
                    self.visits.append(processed)
                    self.stats['visits'] += 1

                    # Group by day if requested
                    if group_by_day and processed['start_time']:
                        date_key = self.get_date_key(processed['start_time'])
                        self.visits_by_day[date_key].append(processed)
        
        print(f"Processed {self.stats['activities']} activities and {self.stats['visits']} visits")
        print(f"Filtered out {self.stats['filtered_out']} entries")
        
        # Generate KML
        print(f"Generating KML file: {output_file}")
        self.write_kml(output_file, group_by_day, include_tracks)

        print("Conversion completed successfully!")
        self.print_stats()

    def write_kml(self, output_file: str, group_by_day: bool = False, include_tracks: bool = True) -> None:
        """Write processed data to KML file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
            f.write('  <Document>\n')
            f.write('    <name><![CDATA[Google Location History]]></name>\n')
            f.write('    <description><![CDATA[Converted from Google Location History JSON]]></description>\n')
            f.write('    <visibility>1</visibility>\n')
            f.write('    <open>1</open>\n')

            # Write styles
            self.write_styles(f)

            if group_by_day:
                # Write data organized by day
                self.write_daily_folders(f)
            else:
                # Write activities folder
                if self.activities:
                    self.write_activities_folder(f)

                # Write visits folder
                if self.visits:
                    self.write_visits_folder(f)

                # Write tracks folder (for non-grouped version)
                if include_tracks:
                    self.write_tracks_folder(f)

            f.write('  </Document>\n')
            f.write('</kml>\n')

    def write_styles(self, f) -> None:
        """Write KML styles for different types of placemarks."""
        styles = {
            'activity_start': {
                'color': 'ff00ff00',  # Green
                'icon': 'https://maps.google.com/mapfiles/kml/pal4/icon56.png'
            },
            'activity_end': {
                'color': 'ff0000ff',  # Red
                'icon': 'https://maps.google.com/mapfiles/kml/pal4/icon56.png'
            },
            'visit': {
                'color': 'ffff0000',  # Blue
                'icon': 'https://maps.google.com/mapfiles/kml/pal4/icon49.png'
            },
            'visit_hierarchy_1': {
                'color': 'ff00ffff',  # Yellow
                'icon': 'https://maps.google.com/mapfiles/kml/pal4/icon49.png'
            }
        }

        # Write track line style (deep blue)
        f.write('    <Style id="track_line">\n')
        f.write('      <LineStyle>\n')
        f.write('        <color>ffcc0000</color>\n')  # Deep blue (AABBGGRR format)
        f.write('        <width>3</width>\n')
        f.write('      </LineStyle>\n')
        f.write('    </Style>\n')

        for style_id, style_props in styles.items():
            f.write(f'    <Style id="{style_id}">\n')
            f.write('      <IconStyle>\n')
            f.write(f'        <color>{style_props["color"]}</color>\n')
            f.write('        <scale>1.0</scale>\n')
            f.write('        <Icon>\n')
            f.write(f'          <href>{style_props["icon"]}</href>\n')
            f.write('        </Icon>\n')
            f.write('        <hotSpot x="0.5" xunits="fraction" y="0.5" yunits="fraction"/>\n')
            f.write('      </IconStyle>\n')
            f.write('      <LabelStyle>\n')
            f.write(f'        <color>{style_props["color"]}</color>\n')
            f.write('        <scale>1.0</scale>\n')
            f.write('      </LabelStyle>\n')
            f.write('    </Style>\n')

    def write_daily_folders(self, f) -> None:
        """Write data organized by daily folders."""
        # Get all unique dates from both activities and visits
        all_dates = set()
        all_dates.update(self.activities_by_day.keys())
        all_dates.update(self.visits_by_day.keys())

        # Sort dates chronologically
        sorted_dates = sorted(all_dates)

        for date_key in sorted_dates:
            f.write(f'    <Folder id="day_{date_key}">\n')
            f.write(f'      <name><![CDATA[{date_key}]]></name>\n')
            f.write('      <visibility>1</visibility>\n')
            f.write(f'      <description><![CDATA[Location data for {date_key}]]></description>\n')

            # Write activities subfolder for this day
            if date_key in self.activities_by_day and self.activities_by_day[date_key]:
                self.write_daily_activities_folder(f, date_key, self.activities_by_day[date_key])

            # Write visits subfolder for this day
            if date_key in self.visits_by_day and self.visits_by_day[date_key]:
                self.write_daily_visits_folder(f, date_key, self.visits_by_day[date_key])

            # Write tracks subfolder for this day
            if date_key in self.tracks_by_day and self.tracks_by_day[date_key]:
                self.write_daily_tracks_folder(f, date_key, self.tracks_by_day[date_key])

            f.write('    </Folder>\n')

    def write_daily_activities_folder(self, f, date_key: str, activities: List[Dict]) -> None:
        """Write activities subfolder for a specific day."""
        f.write('      <Folder id="activities_{}">\n'.format(date_key.replace('-', '_')))
        f.write('        <name><![CDATA[Activities]]></name>\n')
        f.write('        <visibility>0</visibility>\n')
        f.write('        <description><![CDATA[Movement activities for {}]]></description>\n'.format(date_key))

        for activity in activities:
            # Write start point
            if activity['start_coords']:
                self.write_activity_placemark(f, activity, 'start', indent='        ')

            # Write end point
            if activity['end_coords']:
                self.write_activity_placemark(f, activity, 'end', indent='        ')

        f.write('      </Folder>\n')

    def write_daily_visits_folder(self, f, date_key: str, visits: List[Dict]) -> None:
        """Write visits subfolder for a specific day."""
        f.write('      <Folder id="visits_{}">\n'.format(date_key.replace('-', '_')))
        f.write('        <name><![CDATA[Visits]]></name>\n')
        f.write('        <visibility>0</visibility>\n')
        f.write('        <description><![CDATA[Places visited on {}]]></description>\n'.format(date_key))

        for visit in visits:
            self.write_visit_placemark(f, visit, indent='        ')

        f.write('      </Folder>\n')

    def write_daily_tracks_folder(self, f, date_key: str, tracks: List[Dict]) -> None:
        """Write tracks subfolder for a specific day."""
        f.write('      <Folder id="tracks_{}">\n'.format(date_key.replace('-', '_')))
        f.write('        <name><![CDATA[Tracks]]></name>\n')
        f.write('        <visibility>1</visibility>\n')
        f.write('        <description><![CDATA[Movement tracks for {}]]></description>\n'.format(date_key))

        for i, track in enumerate(tracks):
            self.write_track_placemark(f, track, i, indent='        ')

        f.write('      </Folder>\n')

    def write_track_placemark(self, f, track: Dict, track_index: int, indent: str = '      ') -> None:
        """Write a single track placemark (LineString) with real path coordinates."""
        coordinates = track.get('coordinates', [])
        if len(coordinates) < 2:
            return

        # Create track name with time and activity type
        start_time_str = self.format_timestamp_for_kml(track['start_time']) if track['start_time'] else 'Unknown'
        track_name = f"{start_time_str} - {track['activity_type']}"

        f.write(f'{indent}<Placemark>\n')
        f.write(f'{indent}  <name><![CDATA[{track_name}]]></name>\n')

        # Create description
        desc = f"Activity: {track['activity_type']}"
        desc += f"<br/>Track Type: {track.get('track_type', 'unknown').replace('_', ' ').title()}"
        desc += f"<br/>Points: {len(coordinates)}"

        if track['start_time'] and track['end_time']:
            duration = track['end_time'] - track['start_time']
            minutes = duration.total_seconds() / 60
            if minutes >= 60:
                hours = minutes / 60
                desc += f"<br/>Duration: {hours:.1f} hours"
            else:
                desc += f"<br/>Duration: {minutes:.0f} minutes"

        if track.get('distance'):
            desc += f"<br/>Distance: {float(track['distance']):.0f}m"

        f.write(f'{indent}  <description><![CDATA[{desc}]]></description>\n')
        f.write(f'{indent}  <styleUrl>#track_line</styleUrl>\n')
        f.write(f'{indent}  <LineString>\n')
        f.write(f'{indent}    <altitudeMode>clampToGround</altitudeMode>\n')

        # Build coordinate string from all points in the track
        coord_strings = []
        for lat, lon in coordinates:
            coord_strings.append(f'{lon},{lat}')
        coordinates_str = ' '.join(coord_strings)

        f.write(f'{indent}    <coordinates>{coordinates_str}</coordinates>\n')
        f.write(f'{indent}  </LineString>\n')
        f.write(f'{indent}</Placemark>\n')

    def write_tracks_folder(self, f) -> None:
        """Write tracks folder to KML file."""
        if not self.tracks:
            return

        f.write('    <Folder id="tracks">\n')
        f.write('      <name><![CDATA[Tracks]]></name>\n')
        f.write('      <visibility>1</visibility>\n')
        f.write('      <description><![CDATA[Movement tracks between locations]]></description>\n')

        for i, track in enumerate(self.tracks):
            self.write_track_placemark(f, track, i, indent='      ')

        f.write('    </Folder>\n')

    def write_activities_folder(self, f) -> None:
        """Write activities folder to KML file."""
        f.write('    <Folder id="activities">\n')
        f.write('      <name><![CDATA[Activities]]></name>\n')
        f.write('      <visibility>0</visibility>\n')
        f.write('      <description><![CDATA[Movement activities like walking, driving, etc.]]></description>\n')

        for activity in self.activities:
            # Write start point
            if activity['start_coords']:
                self.write_activity_placemark(f, activity, 'start', indent='      ')

            # Write end point
            if activity['end_coords']:
                self.write_activity_placemark(f, activity, 'end', indent='      ')

        f.write('    </Folder>\n')

    def write_activity_placemark(self, f, activity: Dict, point_type: str, indent: str = '      ') -> None:
        """Write a single activity placemark (start or end point)."""
        coords = activity['start_coords'] if point_type == 'start' else activity['end_coords']
        time = activity['start_time'] if point_type == 'start' else activity['end_time']

        if not coords or not time:
            return

        lat, lon = coords
        time_str = self.format_timestamp_for_kml(time)

        f.write(f'{indent}<Placemark>\n')
        f.write(f'{indent}  <name><![CDATA[{time_str}]]></name>\n')

        # Create description
        desc = f"{activity['activity_type']} ({point_type})"
        if activity['distance']:
            desc += f"<br/>Distance: {float(activity['distance']):.0f}m"
        desc += f"<br/>Probability: {activity['probability']:.1%}"

        f.write(f'{indent}  <description><![CDATA[{desc}]]></description>\n')
        f.write(f'{indent}  <styleUrl>#{point_type == "start" and "activity_start" or "activity_end"}</styleUrl>\n')
        f.write(f'{indent}  <Point>\n')
        f.write(f'{indent}    <altitudeMode>clampToGround</altitudeMode>\n')
        f.write(f'{indent}    <coordinates>{lon},{lat}</coordinates>\n')
        f.write(f'{indent}  </Point>\n')
        f.write(f'{indent}</Placemark>\n')

    def write_visits_folder(self, f) -> None:
        """Write visits folder to KML file."""
        f.write('    <Folder id="visits">\n')
        f.write('      <name><![CDATA[Visits]]></name>\n')
        f.write('      <visibility>0</visibility>\n')
        f.write('      <description><![CDATA[Places visited and time spent]]></description>\n')

        for visit in self.visits:
            self.write_visit_placemark(f, visit, indent='      ')

        f.write('    </Folder>\n')

    def write_visit_placemark(self, f, visit: Dict, indent: str = '      ') -> None:
        """Write a single visit placemark."""
        lat, lon = visit['coords']

        # Use start time for the placemark name, fallback to end time
        time = visit['start_time'] or visit['end_time']
        if not time:
            time_str = "Unknown time"
        else:
            time_str = self.format_timestamp_for_kml(time)

        f.write(f'{indent}<Placemark>\n')
        f.write(f'{indent}  <name><![CDATA[{time_str}]]></name>\n')

        # Create description
        desc = f"Type: {visit['semantic_type']}"
        if visit['start_time'] and visit['end_time']:
            duration = visit['end_time'] - visit['start_time']
            hours = duration.total_seconds() / 3600
            if hours >= 1:
                desc += f"<br/>Duration: {hours:.1f} hours"
            else:
                minutes = duration.total_seconds() / 60
                desc += f"<br/>Duration: {minutes:.0f} minutes"

        desc += f"<br/>Probability: {visit['probability']:.1%}"
        if visit['place_id']:
            desc += f"<br/>Place ID: {visit['place_id']}"

        f.write(f'{indent}  <description><![CDATA[{desc}]]></description>\n')

        # Choose style based on hierarchy level
        style = 'visit' if visit['hierarchy_level'] == '0' else 'visit_hierarchy_1'
        f.write(f'{indent}  <styleUrl>#{style}</styleUrl>\n')

        f.write(f'{indent}  <Point>\n')
        f.write(f'{indent}    <altitudeMode>clampToGround</altitudeMode>\n')
        f.write(f'{indent}    <coordinates>{lon},{lat}</coordinates>\n')
        f.write(f'{indent}  </Point>\n')
        f.write(f'{indent}</Placemark>\n')

    def print_stats(self) -> None:
        """Print conversion statistics."""
        print("\n=== Conversion Statistics ===")
        print(f"Total entries processed: {self.stats['total_entries']}")
        print(f"Activities: {self.stats['activities']}")
        print(f"Visits: {self.stats['visits']}")
        print(f"Tracks: {self.stats['tracks']}")
        print(f"Filtered out: {self.stats['filtered_out']}")
        print(f"Total placemarks created: {self.stats['activities'] * 2 + self.stats['visits'] + self.stats['tracks']}")


def parse_date(date_string: str) -> datetime:
    """Parse date string in various formats."""
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S%z'
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: {date_string}")


def main():
    """Main function to handle command line arguments and run conversion."""
    parser = argparse.ArgumentParser(
        description='Convert Google Location History JSON to KML format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s location-history.json output.kml
  %(prog)s location-history.json output.kml --start-date 2024-01-01 --end-date 2024-12-31
  %(prog)s location-history.json output.kml --no-activities
  %(prog)s location-history.json output.kml --no-visits
  %(prog)s location-history.json output.kml --no-tracks
  %(prog)s location-history.json output.kml --group-by-day
  %(prog)s location-history.json output.kml --group-by-day --start-date 2024-01-01
        """
    )

    parser.add_argument('input_file', help='Input Google Location History JSON file')
    parser.add_argument('output_file', help='Output KML file')
    parser.add_argument('--start-date', type=str, help='Start date filter (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date filter (YYYY-MM-DD)')
    parser.add_argument('--min-accuracy', type=float, help='Minimum accuracy threshold (meters)')
    parser.add_argument('--no-activities', action='store_true', help='Exclude activity data')
    parser.add_argument('--no-visits', action='store_true', help='Exclude visit data')
    parser.add_argument('--no-tracks', action='store_true', help='Exclude movement tracks')
    parser.add_argument('--group-by-day', action='store_true', help='Organize data by day (creates daily folders with activities and visits subfolders)')

    args = parser.parse_args()

    # Parse date filters
    start_date = None
    end_date = None

    if args.start_date:
        try:
            start_date = parse_date(args.start_date)
        except ValueError as e:
            print(f"Error parsing start date: {e}", file=sys.stderr)
            sys.exit(1)

    if args.end_date:
        try:
            end_date = parse_date(args.end_date)
        except ValueError as e:
            print(f"Error parsing end date: {e}", file=sys.stderr)
            sys.exit(1)

    # Validate date range
    if start_date and end_date and start_date > end_date:
        print("Error: Start date must be before end date", file=sys.stderr)
        sys.exit(1)

    # Create converter and run conversion
    converter = LocationHistoryConverter()

    try:
        converter.convert_to_kml(
            json_file=args.input_file,
            output_file=args.output_file,
            start_date=start_date,
            end_date=end_date,
            min_accuracy=args.min_accuracy,
            include_activities=not args.no_activities,
            include_visits=not args.no_visits,
            include_tracks=not args.no_tracks,
            group_by_day=args.group_by_day
        )
    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
