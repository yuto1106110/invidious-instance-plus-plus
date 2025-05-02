import json
import requests
from pathlib import Path

# === 設定 ===
FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/eviter-api/databases/(default)/documents/invidious_candidates"

# === ディレクトリ・ファイル準備 ===
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

VALID_FILE = data_dir / "valid.json"
CANDIDATE_FILE = data_dir / "candidates.txt"

# === Firestore から取得して candidates.txt に追加 ===
def fetch_firestore_urls():
    try:
        res = requests.get(FIRESTORE_URL, timeout=5)
        res.raise_for_status()
        documents = res.json().get("documents", [])
        return [
            doc["fields"]["url"]["stringValue"]
            for doc in documents
            if "fields" in doc and "url" in doc["fields"]
        ]
    except Exception as e:
        print("Firestore 取得エラー:", e)
        return []

# === 候補URL読み込み（テキスト形式：1行1URL） ===
existing_candidates = set()
if CANDIDATE_FILE.exists():
    existing_candidates = set(
        line.strip() for line in CANDIDATE_FILE.read_text().splitlines() if line.strip()
    )

# === Firestore URL 追加 ===
firestore_urls = fetch_firestore_urls()
new_urls = [url for url in firestore_urls if url not in existing_candidates]

if new_urls:
    with open(CANDIDATE_FILE, "a", encoding="utf-8") as f:
        for url in new_urls:
            f.write(url + "\n")
    print(f"{len(new_urls)} 件のURLを candidates.txt に追加しました。")
else:
    print("Firestoreからの新規URLはありませんでした。")

# === valid.json を読み込み or 初期化 ===
base_structure = {
    "video": [],
    "search": [],
    "channel": [],
    "playlist": [],
    "comments": []
}
if VALID_FILE.exists():
    try:
        valid_urls = json.loads(VALID_FILE.read_text())
    except json.JSONDecodeError:
        valid_urls = base_structure.copy()
else:
    valid_urls = base_structure.copy()

# === 再度 候補URL 読み込み
candidate_urls = []
if CANDIDATE_FILE.exists():
    candidate_urls = [line.strip() for line in CANDIDATE_FILE.read_text().splitlines() if line.strip()]
else:
    print("candidates.txt が見つかりません。")

# === Invidious判定関数 ===
def is_invidious_instance(url):
    try:
        r = requests.get(url + "/api/v1/stats", timeout=5)
        return r.ok and r.json().get("software") == "invidious"
    except:
        return False

# === 検証と追加処理 ===
for url in candidate_urls:
    print(f"[検証] {url} → ", end="")
    if is_invidious_instance(url):
        print("Invidious")
        for category in valid_urls:
            if url not in valid_urls[category]:
                valid_urls[category].append(url)
    else:
        print("無効")

# === 保存 ===
VALID_FILE.write_text(json.dumps(valid_urls, indent=2, ensure_ascii=False))
print("→ data/valid.json に保存完了。")
