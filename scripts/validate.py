import json
import requests
from pathlib import Path

# === ディレクトリ・ファイル準備 ===
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

VALID_FILE = data_dir / "valid.json"
CANDIDATE_FILE = data_dir / "candidates.txt"

# === 初期形式（カテゴリ別） ===
base_structure = {
    "video": [],
    "search": [],
    "channel": [],
    "playlist": [],
    "comments": []
}

# === valid.json の読み込みまたは初期化 ===
if VALID_FILE.exists():
    try:
        valid_urls = json.loads(VALID_FILE.read_text())
    except:
        valid_urls = base_structure.copy()
else:
    valid_urls = base_structure.copy()

# === Firestoreから新しいURLを取得して candidates.txt に追加 ===
def fetch_from_firestore_and_update_candidates():
    url = "https://firestore.googleapis.com/v1/projects/eviter-api/databases/(default)/documents/invidious_candidates"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        documents = res.json().get("documents", [])
        new_urls = []

        # 既存候補読み込み
        if CANDIDATE_FILE.exists():
            existing = {line.strip() for line in CANDIDATE_FILE.read_text().splitlines()}
        else:
            existing = set()

        for doc in documents:
            fields = doc.get("fields", {})
            raw_url = fields.get("url", {}).get("stringValue", "").strip()
            if raw_url.startswith("http") and raw_url not in existing:
                new_urls.append(raw_url)

        if new_urls:
            with CANDIDATE_FILE.open("a") as f:
                for url in new_urls:
                    f.write(url + "\n")
            print(f"[追加] {len(new_urls)} 件を candidates.txt に追加しました。")
        else:
            print("[追加なし] 新しいURLはありませんでした。")
    except Exception as e:
        print(f"[Firestore取得エラー] {e}")

# === Invidiousインスタンスか判定 ===
def is_invidious(url):
    try:
        r = requests.get(url.rstrip("/") + "/api/v1/stats", timeout=5)
        return r.ok and r.json().get("software") == "invidious"
    except:
        return False

# === URLを検証して valid.json に追加 ===
def validate_candidates():
    if not CANDIDATE_FILE.exists():
        print("candidates.txt が存在しません。")
        return

    urls = [line.strip() for line in CANDIDATE_FILE.read_text().splitlines() if line.strip()]
    for url in urls:
        print(f"[検証] {url} → ", end="")
        if is_invidious(url):
            print("Invidious")
            for cat in valid_urls:
                if url not in valid_urls[cat]:
                    valid_urls[cat].append(url)
        else:
            print("無効")

    VALID_FILE.write_text(json.dumps(valid_urls, indent=2, ensure_ascii=False))
    print("→ valid.json に保存しました。")

# === 実行 ===
fetch_from_firestore_and_update_candidates()
validate_candidates()
