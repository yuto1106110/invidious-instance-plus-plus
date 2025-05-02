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

# Invidiousか判定
def is_invidious(url):
    test_paths = ["/api/v1/stats", "/feed/popular", "/"]  # 複数APIを試す
    for path in test_paths:
        try:
            full_url = url.rstrip("/") + path
            r = requests.get(full_url, timeout=5)
            if r.ok:
                # statsなら software チェック、それ以外なら200で合格
                if "stats" in path:
                    return r.json().get("software") == "invidious"
                return True
        except:
            continue
    return False

# 検証
def validate_candidates():
    if not CANDIDATE_FILE.exists():
        print("candidates.txt が存在しません。")
        return

    urls = [line.strip() for line in CANDIDATE_FILE.read_text().splitlines() if line.strip()]
    for url in urls:
        print(f"[検証中] {url} → ', end='')
        if is_invidious(url):
            print("有効")
            for cat in valid_urls:
                if url not in valid_urls[cat]:
                    valid_urls[cat].append(url)
        else:
            print("× 無効")

    VALID_FILE.write_text(json.dumps(valid_urls, indent=2, ensure_ascii=False))
    print("→ valid.json に保存しました。")

# 実行
fetch_from_firestore_and_update_candidates()
validate_candidates()
