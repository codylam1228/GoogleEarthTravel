<!-- markdownlint-disable first-line-h1 -->
<!-- markdownlint-disable html -->
<!-- markdownlint-disable no-duplicate-header -->

<div align="center">
  <img src="https://i0.wp.com/techpressionmedia.com/wp-content/uploads/2024/02/Google-Earth-1.jpg" width="60%" alt="Google Earth" />
</div>

# 旅遊軌跡記錄與 Google Earth 操作流程

本專案提供一個本機化流程，將旅遊位置資料轉換為 KML 檔案，並使用 Google Earth 顯示。

本專案支援兩種輸入來源：

- 從 iPhone 或 Apple Watch 的 **Open GPX Tracker** 匯出的 **GPX 檔案**
- 從 **Google Maps Timeline** 匯出的 **JSON 檔案**

此流程不需要雲端資料庫、持續運行的伺服器、Docker 或第三方線上轉檔服務。所有轉換均在本機電腦完成。

```text
Open GPX Tracker / Google Maps Timeline
                ↓
匯出 GPX 或 JSON 檔案
                ↓
將檔案放入 input/
                ↓
使用 uv 執行 convert.py
                ↓
在 output/ 產生 KML 檔案
                ↓
將 KML 匯入 Google Earth
```

## 支援的輸入格式

| 輸入格式 | 來源 | KML 輸出內容 |
|---|---|---|
| `.gpx` | Open GPX Tracker | GPS 軌跡線及手動加入的地點標記 |
| `.json` | Google Maps Timeline 匯出資料 | 活動起點／終點連線及停留地點標記 |

> [!NOTE]
> GPX 檔案包含詳細的 GPS trackpoints，因此其 KML 輸出能代表實際記錄到的移動路線。
>
> 目前支援的 Google Maps Timeline JSON 格式通常只有活動的起點和終點座標。因此，每段活動會顯示為直線，而不是實際道路、鐵路或步行路線。

## 先決條件

使用本專案前，請先準備以下項目：

- 如要記錄新的旅程：已安裝 [Open GPX Tracker](https://apps.apple.com/us/app/open-gpx-tracker/id984503772) 的 iPhone 或 Apple Watch
- 已安裝 [uv](https://docs.astral.sh/uv/) 的電腦
- Google Earth Web 或 Google Earth Pro
- 本專案 Repository，包含 `convert.py`

Google Earth 支援開啟本機 KML 檔案，也可以將 KML/KMZ 資料匯入 Google Earth Project。

## 專案結構

專案目錄必須使用以下結構：

```text
GoogleEarthTravel/
├── input/          # 放入 GPX 或 Google Timeline JSON 檔案
├── output/         # 產生的 KML 檔案會儲存在此處
├── archive/        # 成功處理的來源檔案會移至此處
├── convert.py      # GPX/JSON 轉換為 KML 的腳本
├── pyproject.toml
└── uv.lock
```

如果資料夾尚未建立，請先建立所需資料夾。

### macOS / Linux

```bash
mkdir -p input output archive
```

### Windows PowerShell

```powershell
mkdir input, output, archive
```

## 初始設定

在專案根目錄執行以下指令，以安裝專案相依套件：

```bash
uv sync
```

如果 `pyproject.toml` 尚未包含所需套件，可執行：

```bash
uv add gpxpy simplekml
```

## SOP：記錄旅遊軌跡

本節適用於使用 Open GPX Tracker 記錄的新旅程。

### 步驟 1：建立軌跡

1. 在 iPhone 或 Apple Watch 開啟 **Open GPX Tracker**。
2. 建立一條新的軌跡。
3. 為軌跡設定有意義的名稱。

範例：

```text
2026-07-16_Tokyo_Asakusa-Shibuya
```

4. 在旅程開始前按下 **Record** 或 **Start**。

### 步驟 2：加入地點標記

在旅程途中，每當到達重要位置時，請加入一個 waypoint（地點標記）。

建議的地點類型：

- 酒店
- 機場
- 火車站
- 餐廳
- 旅遊景點
- 行山檢查點
- 集合地點

建議的地點名稱：

```text
Hotel Check-in
Tokyo Station
Lunch - Sushi Restaurant
Senso-ji Temple
Shibuya Crossing
```

這些 waypoint 會連同 GPX 檔案一同匯出，並於 Google Earth 顯示為地點標記。

### 步驟 3：停止並儲存

旅程結束後：

1. 停止記錄。
2. 儲存軌跡。
3. 如有需要，檢查軌跡和 waypoint。
4. 將完成的軌跡匯出成 GPX 檔案。

建議檔案命名格式：

```text
YYYY-MM-DD_城市_行程名稱.gpx
```

範例：

```text
2026-07-16_Tokyo_Asakusa-Shibuya.gpx
2026-07-17_Tokyo_Kamakura-DayTrip.gpx
2026-07-18_Okinawa_Naha-Walk.gpx
```

## SOP：從 Open GPX Tracker 匯出 GPX

1. 在 Open GPX Tracker 開啟已完成的軌跡。
2. 選擇 **Share** 或 **Export**。
3. 選擇 **GPX** 格式。
4. 透過 AirDrop、iCloud Drive、Files、電子郵件或 USB 將檔案傳送到電腦。
5. 將匯出的 `.gpx` 檔案複製到專案的 `input/` 資料夾。

範例：

```text
GoogleEarthTravel/
└── input/
    └── 2026-07-16_Tokyo_Asakusa-Shibuya.gpx
```

## SOP：匯出 Google Timeline JSON

本節適用於從 Google Maps Timeline 匯入歷史位置資料。

1. 在手機裝置上開啟 Google Maps Timeline 設定。
2. 將 Timeline 資料匯出成 JSON 檔案。
3. 將匯出的 JSON 檔案傳送到電腦。
4. 將 `.json` 檔案複製到專案的 `input/` 資料夾。

範例：

```text
GoogleEarthTravel/
└── input/
    └── location-history.json
```

目前支援的 Google Timeline JSON 結構，最外層是一個 JSON array，並包含類似以下的紀錄：

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
> 請不要修改、截斷，或只複製匯出的 JSON 檔案其中一部分。
>
> 來源檔案必須是完整且有效的 JSON，並以 `[` 開始、以 `]` 結束。

## SOP：將 GPX 或 JSON 轉為 KML

把一個或多個支援的檔案放進 `input/`。

範例：

```text
GoogleEarthTravel/
├── input/
│   ├── 2026-07-16_Tokyo_Asakusa-Shibuya.gpx
│   └── location-history.json
├── output/
├── archive/
└── convert.py
```

在專案根目錄執行轉換程式：

```bash
uv run python convert.py
```

程式會自動：

1. 尋找 `input/` 內所有 `.gpx` 和 `.json` 檔案。
2. 自動識別每個檔案的格式。
3. 將每個支援的檔案轉換成獨立的 KML 檔案。
4. 將產生的 KML 檔案儲存在 `output/`。
5. 將成功處理的來源檔案移至 `archive/`。
6. 把轉換失敗的來源檔案保留在 `input/`，以便排錯。

終端機輸出範例：

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

## 輸出與封存

成功轉換後，目錄結構會類似以下：

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

來源檔案只有在成功產生有效且非空的 KML 檔案後，才會被移到 `archive/`。

如果轉換失敗，來源檔案會保留在 `input/`。

## SOP：將 KML 匯入 Google Earth

### Google Earth Web

1. 開啟 [Google Earth](https://earth.google.com/web/)。
2. 建立新的 Project，或開啟現有 Project。
3. 選擇 **New feature** 或 **Import file**。
4. 從 `output/` 資料夾選擇 `.kml` 檔案。
5. 等待檔案完成載入。
6. 如有需要，儲存 Google Earth Project。

### Google Earth Pro

1. 開啟 Google Earth Pro。
2. 選擇 **File** → **Open**。
3. 從 `output/` 資料夾選擇 `.kml` 檔案。
4. KML 內容會出現在左側的 **Places** 面板。
5. 如要在重啟 Google Earth Pro 後保留資料，請將已匯入項目拖曳至 **My Places**。

## KML 結構：GPX 檔案

從 GPX 產生的 KML 包含獨立的軌跡和 waypoint 資料夾。

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

因此，你可以在 Google Earth 中分別顯示或隱藏路線和地點標記。

## KML 結構：Timeline JSON

從 Google Timeline JSON 產生的 KML 包含獨立的活動和停留地點資料夾。

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

### 活動輸出內容

每個 Timeline activity 包含：

- 開始與結束時間
- 活動類型，例如 `in passenger vehicle` 或 `in subway`
- Google 信心分數
- 預估距離
- 由起點與終點座標連成的直線

### 停留地點輸出內容

每個 Timeline visit 包含：

- 到達與離開時間
- 停留時長
- Semantic type（如資料有提供）
- Google Place ID（如資料有提供）
- Google 信心分數
- 停留位置標記

## 重要注意事項

- 請只在旅程開始時才啟動 GPX 記錄，以減少不必要的 GPS 點和電池消耗。
- 旅程結束後應立即停止記錄。
- 在室內、地下、隧道或高密度高樓區域，GPS 準確度可能降低。
- 記錄 GPX 時，建議使用 waypoint 標記重要位置。
- 建議每一天或每項活動儲存成一個獨立 GPX 檔案，方便後續管理。
- 請保留 `archive/` 中的原始 GPX 和 JSON 檔案作為來源資料。
- 腳本只會處理直接放在 `input/` 內的檔案，不會掃描子資料夾。
- 腳本支援 `.gpx`、`.GPX`、`.json` 及 `.JSON` 副檔名。
- GPX 輸出能顯示詳細路線，因為 GPX 包含完整的 trackpoints。
- Google Timeline JSON 輸出可能顯示為直線，因為匯出的 activity 紀錄可能只包含起點和終點座標。
- 產生的 KML 檔案亦可用支援 KML 的 GIS 工具開啟，例如 QGIS。

## 疑難排解

### 找不到檔案

請確認來源檔案直接放在：

```text
GoogleEarthTravel/input/
```

支援的副檔名包括：

```text
.gpx
.GPX
.json
.JSON
```

### 同一檔案被處理兩次

請確認你使用的是最新版本的 `convert.py`。

此腳本只會掃描一次 `input/`，並以不區分大小寫的方式檢查副檔名，避免 Windows 將 `.gpx` 和 `.GPX` 視為不同匹配結果。

### JSON 轉換失敗

請檢查 JSON 檔案是否完整且有效。

有效的 Timeline JSON 匯出檔應符合以下條件：

- 以 `[` 開始
- 以 `]` 結束
- 內含完整 JSON object
- 包含 `activity` 和／或 `visit` 紀錄
- 包含 `geo:緯度,經度` 格式的座標值

### Google Earth 顯示為直線

這是部分 Google Maps Timeline JSON 匯出格式的預期行為。

該檔案可能只包含 activity 的起始座標和結束座標，而不包含中間的 GPS trackpoints。若未來需要更詳細、貼近實際移動的路線幾何，建議使用 Open GPX Tracker 記錄。

## 使用技術

- [Open GPX Tracker](https://apps.apple.com/us/app/open-gpx-tracker/id984503772)
- [uv](https://docs.astral.sh/uv/)
    - Python
        - [gpxpy](https://github.com/tkrajina/gpxpy)
        - [simplekml](https://simplekml.readthedocs.io/)
- Google Maps Timeline
- Google Earth