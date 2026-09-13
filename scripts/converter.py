import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime, timedelta

# --- 1. GPX 轉 KML ---
def convert_gpx_to_kml(gpx_string: str) -> str:
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    try:
        root = ET.fromstring(gpx_string)
    except Exception as e:
        return f"Error parsing GPX: {str(e)}"

    kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Google Earth Travel Track</name>
    <Style id="trackStyle">
      <LineStyle><color>ff0000ff</color><width>4</width></LineStyle>
    </Style>
"""
    kml_footer = "  </Document>\n</kml>"
    kml_body = []

    # Waypoints
    for wpt in root.findall('gpx:wpt', ns):
        lat, lon = wpt.attrib.get('lat'), wpt.attrib.get('lon')
        name_elem = wpt.find('gpx:name', ns)
        name = name_elem.text if name_elem is not None else "Waypoint"
        kml_body.append(f"""    <Placemark>
      <name>{name}</name>
      <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>""")

    # Track Points
    for trk in root.findall('gpx:trk', ns):
        for trkseg in trk.findall('gpx:trkseg', ns):
            coords = []
            for trkpt in trkseg.findall('gpx:trkpt', ns):
                lat, lon = trkpt.attrib.get('lat'), trkpt.attrib.get('lon')
                coords.append(f"{lon},{lat},0")
            coord_str = " ".join(coords)
            kml_body.append(f"""    <Placemark>
      <name>Route Track</name>
      <styleUrl>#trackStyle</styleUrl>
      <LineString><tessellate>1</tessellate><coordinates>{coord_str}</coordinates></LineString>
    </Placemark>""")

    return kml_header + "\n".join(kml_body) + "\n" + kml_footer

# --- 2. Google Timeline JSON 轉 KML ---
def convert_timeline_json_to_kml(json_string: str) -> str:
    try:
        data = json.loads(json_string)
    except Exception as e:
        return f"Error parsing JSON: {str(e)}"

    kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Google Timeline Track</name>
"""
    kml_footer = "  </Document>\n</kml>"
    kml_body = []

    for item in data:
        if "activity" in item:
            act = item["activity"]
            start_geo, end_geo = act.get("start", ""), act.get("end", "")
            if start_geo.startswith("geo:") and end_geo.startswith("geo:"):
                s_lat, s_lon = start_geo[4:].split(",")
                e_lat, e_lon = end_geo[4:].split(",")
                kml_body.append(f"""    <Placemark>
      <name>Activity</name>
      <LineString><coordinates>{s_lon},{s_lat},0 {e_lon},{e_lat},0</coordinates></LineString>
    </Placemark>""")
        elif "visit" in item:
            visit = item["visit"]
            cand = visit.get("topCandidate", {})
            loc = cand.get("placeLocation", "")
            if loc.startswith("geo:"):
                lat, lon = loc[4:].split(",")
                kml_body.append(f"""    <Placemark>
      <name>Visit</name>
      <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>""")

    return kml_header + "\n".join(kml_body) + "\n" + kml_footer

# --- 3. KML 工具：按日期剪裁 (Prune by Date) ---
def prune_kml_by_date(kml_string: str, target_date_str: str) -> str:
    try:
        root = ET.fromstring(kml_string)
    except Exception as e:
        return f"Error: {str(e)}"
    
    # 簡易清理非目標日期的 Placemark
    ns = "{http://www.opengis.net/kml/2.2}"
    for doc in root.findall(f'{ns}Document'):
        for pm in list(doc.findall(f'{ns}Placemark')):
            desc = pm.find(f'{ns}description')
            text = desc.text if desc is not None else ""
            if target_date_str not in text:
                doc.remove(pm)
    return ET.tostring(root, encoding='unicode')