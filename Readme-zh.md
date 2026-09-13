<!-- markdownlint-disable first-line-h1 -->
<!-- markdownlint-disable html -->
<!-- markdownlint-disable no-duplicate-header -->

<div align="center">
  <img src="https://i0.wp.com/techpressionmedia.com/wp-content/uploads/2024/02/Google-Earth-1.jpg" width="60%" alt="Google Earth" />
</div>

# 旅遊軌跡記錄與 Google Earth 操作流程

本專案提供本機與網頁端的完整流程，用於將旅遊軌跡資料轉換、剪裁、修復及切分為 KML 檔案，並使用 Google Earth 進行檢視。

支援功能：
- **GPX 檔案**（從 Open GPX Tracker 匯出）
- **JSON 檔案**（從 Google Maps Timeline 匯出）
- **KML 工具鏈**：依日期剪裁、修復碎片化軌跡、切分大型軌跡。

---

## 🌐 網頁版應用程式 (Pyodide WASM)

無需安裝 Python，直接在瀏覽器中使用：
👉 **[開啟全功能網頁工具](https://codylam1228.github.io/GoogleEarthTravel/)**

特點：
- **100% 本地端處理**：基於 Pyodide WebAssembly 技術，所有資料轉換皆在瀏覽器完成，絕不傳送至伺服器。
- **雙語介面**：支援繁體中文與英文一鍵切換。