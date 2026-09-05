# Ghost Engine: Taiwan — Instagram Reels 自動發文

自動發布 Instagram Reels 給 **The Ghost Engine: Taiwan**（IG [@taiwanlore.yt](https://www.instagram.com/taiwanlore.yt/)），
用英文講述台灣鬼故事／地方傳說／民間信仰，與 YouTube 頻道 [@GhostEngine.Taiwan](https://www.youtube.com/@GhostEngine.Taiwan) 同步。

這是獨立專案，跟 Threads 機器人（@johny800333）分開，帳號、Meta App、credentials 都不共用。

## 架構

- 影片檔案（9:16 直式、已燒字幕）透過 **GitHub Release** 附件託管，取得公開可下載的網址
  （Instagram Graph API 只接受公開影片網址，不接受直接上傳）
- `config/queue.json`：待發布佇列，每筆包含 `video_url`、`caption`、`status`
- `scripts/publish_next.py`：每次執行只發佈佇列裡「下一筆」pending 的項目，
  發布成功後把該筆標記為 `published`（含 media_id、時間戳），並寫回 `queue.json`
- `.github/workflows/publish.yml`：GitHub Actions 排程（cron，可調整），
  每次觸發呼叫 `publish_next.py`，發布後自動 commit 更新後的 `queue.json`
- `src/instagram_uploader.py`：實作 Instagram Graph API 兩段式 Reels 發布流程
  1. `POST /{ig-user-id}/media`（`media_type=REELS` + `video_url` + `caption`）→ `creation_id`
  2. 輪詢 `GET /{creation_id}?fields=status_code` 直到 `FINISHED`
  3. `POST /{ig-user-id}/media_publish`（`creation_id`）→ 正式發布

## 設定（一次性）

1. Repo Settings → Secrets and variables → Actions，新增兩個 secrets：
   - `IG_ACCESS_TOKEN`：長效存取權杖（Instagram Login flow，`instagram_business_content_publish` scope）
   - `IG_BUSINESS_ACCOUNT_ID`：`17841437752957107`（@taiwanlore.yt 的 IGSID）
2. 影片素材上傳到對應集數的 GitHub Release（本集 tag：`ep01-kenting-baobao-princess`），
   並在 `config/queue.json` 填入對應的 release download URL + 文案
3. Actions 分頁確認 workflow 已啟用；也可以手動觸發（workflow_dispatch）測試單次發布

## 新增一批內容（之後每週）

1. 把新一批影片建立成新的 GitHub Release（新的 tag，例如 `ep02-xxx`），上傳影片附件
2. 把新項目（`video_url` 指向新 release 的下載連結、對應文案）加進 `config/queue.json` 的 `items` 陣列
3. 排程會依序（由上到下）發布 `status: "pending"` 的項目，一次一支
