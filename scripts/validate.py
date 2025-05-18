import json
import requests
from pathlib import Path

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
VALID_FILE = data_dir / "valid.json"
CANDIDATE_FILE = data_dir / "candidates.txt"

base_structure = {
    "video": [],
    "search": [],
    "channel": [],
    "playlist": [],
    "comments": []
}

# valid.json読み込み
if VALID_FILE.exists():
    try:
        valid_urls = json.loads(VALID_FILE.read_text())
    except:
        valid_urls = base_structure.copy()
else:
    valid_urls = base_structure.copy()

# Firestoreから取得
def fetch_from_firestore_and_update_candidates():
    url = "https://firestore.googleapis.com/v1/projects/eviter-api/databases/(default)/documents/invidious_candidates"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        documents = res.json().get("documents", [])
        new_urls = []

        if CANDIDATE_FILE.exists():
            existing = {line.strip() for line in CANDIDATE_FILE.read_text().splitlines()}
        else:
            existing = set()

        for doc in documents:
            raw_url = doc.get("fields", {}).get("url", {}).get("stringValue", "").strip()
            if raw_url.startswith("http") and raw_url not in existing:
                new_urls.append(raw_url)

        if new_urls:
            with CANDIDATE_FILE.open("a") as f:
                for url in new_urls:
                    f.write(url + "\n")
            print(f"[追加] {len(new_urls)} 件追加")
        else:
            print("[追加なし]")
    except Exception as e:
        print(f"[Firestore取得エラー] {e}")

# 再生できるか確認
def is_playable_video(url):
    try:
        res = requests.get(url.rstrip("/") + "/api/v1/videos/RgKAFK5djSk", timeout=5)
        if not res.ok:
            return False
        data = res.json()
        for key in ['formatStreams', 'adaptiveFormats', 'videoStreams']:
            if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                if 'url' in data[key][0]:
                    stream_url = data[key][0]['url']
                    video_res = requests.get(stream_url, timeout=3)
                    return 'video' in video_res.headers.get("Content-Type", "")
        if 'hlsUrl' in data:
            video_res = requests.get(data['hlsUrl'], timeout=3)
            return 'video' in video_res.headers.get("Content-Type", "")
    except:
        return False
    return False

# コメント取得できるか
def has_comments(url):
    try:
        res = requests.get(url.rstrip("/") + "/api/v1/comments/RgKAFK5djSk", timeout=5)
        data = res.json()
        return isinstance(data, dict) and "comments" in data and len(data["comments"]) > 0
    except:
        return False

# 検証と保存
def validate_candidates():
    if not CANDIDATE_FILE.exists():
        print("candidates.txt が存在しません。")
        return

    urls = [line.strip() for line in CANDIDATE_FILE.read_text().splitlines() if line.strip()]
    for url in urls:
        print(f"[検証中] {url}")
        video_ok = is_playable_video(url)
        comments_ok = has_comments(url)

        if video_ok and comments_ok:
            print("  → 動画・コメントOK → 採用")
            for cat in base_structure:
                if url not in valid_urls[cat]:
                    valid_urls[cat].append(url)
        else:
            print(f"  → 動画: {video_ok}, コメント: {comments_ok} → 除外")

    json_text = json.dumps(valid_urls, indent=2, ensure_ascii=False)
    json_text = json_text.replace('"', "'")
    VALID_FILE.write_text(json_text, encoding="utf-8")
    print("→ valid.json に保存しました（動画＋コメント再生確認済み）")

# 実行
fetch_from_firestore_and_update_candidates()
validate_candidates()
