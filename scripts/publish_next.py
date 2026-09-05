#!/usr/bin/env python3
"""
Publishes the next pending item in config/queue.json as an Instagram Reel,
then marks it as published (with timestamp + media id) and writes the
queue file back so the next scheduled run picks up the following item.

Meant to be run from GitHub Actions (see .github/workflows/publish.yml),
which commits the updated queue.json back to the repo after a successful
run.
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from instagram_uploader import publish_reel  # noqa: E402

QUEUE_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "queue.json")


def main():
    with open(QUEUE_PATH, "r", encoding="utf-8") as f:
        queue = json.load(f)

    items = queue["items"]
    next_item = next((it for it in items if it["status"] == "pending"), None)

    if next_item is None:
        print("No pending items in queue.json — nothing to publish.")
        return

    print(f"Publishing {next_item['id']} ({next_item['video_url']})")
    media_id = publish_reel(next_item["video_url"], next_item["caption"])

    next_item["status"] = "published"
    next_item["published_at"] = datetime.now(timezone.utc).isoformat()
    next_item["media_id"] = media_id

    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Done. {next_item['id']} marked as published.")


if __name__ == "__main__":
    main()
