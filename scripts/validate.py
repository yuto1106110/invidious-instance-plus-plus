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

# valid.jsonの初期読み込み
if VALID_FILE.exists():
    try:
        valid_urls = json.loads(VALID_FILE.read_text())
    except:
        valid_urls = base_structure.copy()
else:
    valid_urls = base_structure.copy()

# Firestoreから新規取得
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
            print("[追加なし] 新しいURLはありません")
    except Exception as e:
        print(f"[Firestore取得エラー] {e}")

# 柔軟にInvidiousインスタンス判定
def is_invidious(url):
    try:
        stats_url = url.rstrip("/") + "/api/v1/stats"
        r = requests.get(stats_url, timeout=5)
        if r.ok and r.headers.get("content-type", "").startswith("application/json"):
            data = r.json()
            if "version" in data or "software" in data or "totalVideos" in data:
                return True
    except:
        pass

    try:
        feed_url = url.rstrip("/") + "/feed/popular"
        r = requests.get(feed_url, timeout=5)
        if r.ok and "Invidious" in r.text:
            return True
    except:
        pass

    return False

# 各カテゴリのAPIチェック（video / comments は内容チェック付き）
def check_category(url, endpoint):
    try:
        test_urls = {
            "video": "/api/v1/videos/RgKAFK5djSk",
            "search": "/api/v1/search?q=test",
            "channel": "/api/v1/channels/UCBR8-60-B28hp2BmDPdntcQ",
            "playlist": "/api/v1/playlists/PLrEnWoR732-D67iteOI6DPdJH1opjAuJt",
            "comments": "/api/v1/comments/RgKAFK5djSk"
        }
        full_url = url.rstrip("/") + test_urls[endpoint]
        r = requests.get(full_url, timeout=7)
        if not r.ok:
            return False

        data = r.json()
        if endpoint == "video":
            return "title" in data and ("hlsUrl" in data or "formatStreams" in data or "adaptiveFormats" in data)
        elif endpoint == "comments":
            return isinstance(data, dict) and "comments" in data and len(data["comments"]) > 0
        else:
            return True  # search, channel, playlist はレスポンス成功ならOK
    except:
        return False

# 候補検証と保存
def validate_candidates():
    if not CANDIDATE_FILE.exists():
        print("candidates.txt が存在しません。")
        return

    urls = [line.strip() for line in CANDIDATE_FILE.read_text().splitlines() if line.strip()]
    filtered_urls = []

    for url in urls:
        print(f"[検証中] {url}")
        if not is_invidious(url):
            print("  → Invidiousではありません（除外）")
            continue

        video_ok = check_category(url, "video")
        comments_ok = check_category(url, "comments")

        if video_ok and comments_ok:
            print("  → video/comments OK → 採用")
            filtered_urls.append(url)
            for cat in base_structure:
                if check_category(url, cat):
                    if url not in valid_urls[cat]:
                        valid_urls[cat].append(url)
        else:
            print(f"  → video:{video_ok}, comments:{comments_ok} → 除外")

    json_text = json.dumps(valid_urls, indent=2, ensure_ascii=False)
    json_text = json_text.replace('"', "'")
    VALID_FILE.write_text(json_text, encoding="utf-8")
    print("→ valid.json に保存しました（video + comments 検証済）")

# 実行
fetch_from_firestore_and_update_candidates()
validate_candidates()
