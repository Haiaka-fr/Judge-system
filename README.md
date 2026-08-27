# Club Online Judge System - 社團線上程式批改系統

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![C++](https://img.shields.io/badge/C++-11/14/17-00599C.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## Description

專門設計為 Python 評分的系統。

---

## Features

* **支援語言**：支援 Python 程式碼，自動比對測資並輸出結果。
* **系統安全與限制**：
  * **Time Limit Exceeded (TLE)**：限制子進程（Subprocess）執行時間，防止死迴圈消耗伺服器資源。
  * **Memory Limit Exceeded (MLE) / Runtime Error (RE)**：捕捉程式執行期異常與記憶體溢出。

---

## Tech Stack

* **核心語言 (Languages)**：Python 3.x（系統核心與調度邏輯）、C++（測試標的與底層比對）
* **核心模組 (Modules/Libraries)**：
  * `subprocess`：管理外部程式編譯與獨立進程執行
  * `sys` / `os`：系統資源控制與檔案路徑處理
  * `json`：測資檔與批改結果資料結構化
* **開發工具 (Dev Tools)**：VS Code, Git, Linux Terminal

---
