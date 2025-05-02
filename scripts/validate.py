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

# カテゴリ別APIパス
category_paths = {
    "video": "/api/v1/videos/3PMZodtM2bE",  # 適当な動画ID
    "search": "/api/v1/search?q=music",
    "channel": "/api/v1/channels/UCBR8-60-B28hp2BmDPdntcQ",  # YouTube公式
    "playlist": "/api/v1/playlists/PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI",  # 適当なプレイリスト
    "comments": "/api/v1/comments/3PMZodtM2bE"
}

# URLが対応しているカテゴリを判定
def get_valid_categories(url):
    supported = []
    for category, path in category_paths.items():
        try:
            r = requests.get(url.rstrip("/") + path, timeout=5)
            if r.ok:
                supported.append(category)
        except:
            continue
    return supported

# 検証と保存
def validate_candidates():
    if not CANDIDATE_FILE.exists():
        print("candidates.txt が存在しません。")
        return

    urls = [line.strip() for line in CANDIDATE_FILE.read_text().splitlines() if line.strip()]
    for url in urls:
        print(f"[検証中] {url}")
        categories = get_valid_categories(url)
        if categories:
            print(f"  → 対応カテゴリ: {', '.join(categories)}")
            for cat in categories:
                if url not in valid_urls[cat]:
                    valid_urls[cat].append(url)
        else:
            print("  × 無効または非対応")

    # ダブルクォート → シングルクォートに変換して保存
    json_text = json.dumps(valid_urls, indent=2, ensure_ascii=False)
    json_text = json_text.replace('"', "'")
    VALID_FILE.write_text(json_text, encoding="utf-8")
    print("→ valid.json に保存しました。（シングルクォート形式）")

# 実行
fetch_from_firestore_and_update_candidates()
validate_candidates()
