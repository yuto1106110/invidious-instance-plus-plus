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

# valid.json の読み込み
if VALID_FILE.exists():
    try:
        valid_urls = json.loads(VALID_FILE.read_text())
    except:
        valid_urls = base_structure.copy()
else:
    valid_urls = base_structure.copy()

# Invidiousか判定
def is_invidious(url):
    try:
        stats_url = url.rstrip("/") + "/api/v1/stats"
        res = requests.get(stats_url, timeout=5)
        return res.ok and res.json().get("software") == "invidious"
    except:
        return False

# video APIがタイムアウトせず応答するか
def is_video_api_responsive(url, video_id="Ks-_Mh1QhMc"):
    try:
        test_url = url.rstrip("/") + f"/api/v1/videos/{video_id}"
        res = requests.get(test_url, timeout=5)
        return res.ok and res.headers.get("content-type", "").startswith("application/json")
    except:
        return False

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
            print("[追加なし] 新しいURLはありません")
    except Exception as e:
        print(f"[Firestore取得エラー] {e}")

# 検証と保存
def validate_candidates():
    if not CANDIDATE_FILE.exists():
        print("candidates.txt が存在しません。")
        return

    urls = [line.strip() for line in CANDIDATE_FILE.read_text().splitlines() if line.strip()]
    for url in urls:
        print(f"[検証中] {url} → ", end="")
        if is_invidious(url):
            if is_video_api_responsive(url):
                print("有効（video API OK）")
                for cat in valid_urls:
                    if url not in valid_urls[cat]:
                        valid_urls[cat].append(url)
            else:
                print("video API 応答なし → 無効")
        else:
            print("× Invidiousではない")

    # JSON保存（シングルクォート形式）
    json_text = json.dumps(valid_urls, indent=2, ensure_ascii=False)
    json_text = json_text.replace('"', "'")
    VALID_FILE.write_text(json_text, encoding="utf-8")
    print("→ valid.json に保存しました")

# 実行
fetch_from_firestore_and_update_candidates()
validate_candidates()
