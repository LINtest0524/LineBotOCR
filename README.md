# LineBotOCR (Line Translator Bot)

一個 LINE 機器人，支援翻譯英文單字、查音標、播放發音。

## ✨ 功能

- 使用 googletrans 將英文翻譯為中文
- 查詢 dictionaryapi.dev 提供的 IPA 音標與語音連結
- 將 IPA 音標轉換為 KK 音標（內建對照表）
- 使用 LINE Flex Message 呈現字卡介面
- 限制每次最多處理 10 個單字

---

## 🚀 Render 部署指南

### ✅ 須知：
本專案需配合 `LINE_CHANNEL_ACCESS_TOKEN` 才能正確運行。

### 1. 指定 Python 版本
請新增一個檔案 `runtime.txt`，內容為：

