<!-- markdownlint-disable first-line-h1 -->
<!-- markdownlint-disable html -->
<!-- markdownlint-disable no-duplicate-header -->
<div align="center">
  <img src="https://i0.wp.com/techpressionmedia.com/wp-content/uploads/2024/02/Google-Earth-1.jpg" width="60%" alt="Google Earth" />
</div>

## Overview
- This project is tutorial for the google map timeline issue. Also provide a simple tool about converting the json file to kml file.

## Precursor
- You need to turn on the google map timeline [https://support.google.com/maps/answer/6258979?hl=en&co=GENIE.Platform%3DAndroid]



## How does it work?
Step 1: 

Put the location-history.json download from google map timeline
How? Your phone can export a JSON file with the Timeline data it has, similar to the old Takeout.
Android: Go to device Settings > Location > Location Services > Timeline > "Export Timeline data" button"
Simular to Iphone [https://support.google.com/maps/thread/264641290/export-full-location-timeline-data-in-json-or-similar-format-in-the-new-version-of-timeline?hl=en]

---
Step 2: 

use the location_history_json_to_kml.py convert locaton_history.json to output.kml
If the code error occur, please use the [https://www.gpsvisualizer.com/map_input?form=googleearth]

General map parameters->Output file type: kml

Waypoint options->Waypoint labels: Labels on waypoints + tickmarks + trackpoints

Labels on waypoints + tickmarks + trackpoints-> Upload the json file

Then Create KML file and downlaod the KML file

---
Step 3: 

Set up a new project from Google Earth [https://earth.google.com/web/]
Import the KML file to the project
Since the data from google map are not able to choose the time, you need to remove the unwanted data.
In some unexpected cases the line will be missed, so you may also need to add the missing line.


---
## What we used?
- google map 
- google earth 
- gpsvisualizer

Reference:

用 Google Maps 自動規畫路徑的方法
```https://medium.com/fogofworld-hant/%E7%94%A8-google-maps-%E8%87%AA%E5%8B%95%E8%A6%8F%E7%95%AB%E8%B7%AF%E5%BE%91%E7%9A%84%E6%96%B9%E6%B3%95-3eac7fcfb6bb```

用 Google Earth 補交通運輸路徑的方法
```https://medium.com/fogofworld-hant/%E7%94%A8-google-earth-%E8%A3%9C%E4%BA%A4%E9%80%9A%E9%81%8B%E8%BC%B8%E8%B7%AF%E5%BE%91%E7%9A%84%E6%96%B9%E6%B3%95-e1f96fda552f```

Json to kml
```https://www.gpsvisualizer.com/map_input?form=googleearth```

用 FlightAware 補飛機路徑的方法
```https://medium.com/fogofworld-hant/%E7%94%A8-flightaware-%E8%A3%9C%E9%A3%9B%E6%A9%9F%E8%B7%AF%E5%BE%91%E7%9A%84%E6%96%B9%E6%B3%95-5d323057ad4a```
