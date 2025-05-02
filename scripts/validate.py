import json
import requests
from pathlib import Path

# === FirestoreのURL ===
FIRESTORE_API = "https://firestore.googleapis.com/v1/projects/eviter-api/databases/(default)/documents/invidious_candidates"

# === ディレクトリとファイルのパス ===
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

VALID_FILE = data_dir / "valid.json"
CANDIDATE_FILE = data_dir / "candidates.txt"

# === 初期構造（カテゴリごと）===
base_structure = {
    "video": [],
    "search": [],
    "channel": [],
    "playlist": [],
    "comments": []
}

# === valid.json を読み込み or 初期化 ===
if VALID_FILE.exists():
    try:
        valid_urls = json.loads(VALID_FILE.read_text())
    except json.JSONDecodeError:
        valid_urls = base_structure.copy()
else:
    valid_urls = base_structure.copy()

# === FirestoreからURL取得 ===
def fetch_candidate_urls():
    try:
        res = requests.get(FIRESTORE_API)
        res.raise_for_status()
        data = res.json()
        urls = []
        for doc in data.get("documents", []):
            fields = doc.get("fields", {})
            url = fields.get("url", {}).get("stringValue", "")
            if url:
                urls.append(url.strip())
        return urls
    except Exception as e:
        print(f"[エラー] Firestore取得失敗: {e}")
        return []

# === Invidiousインスタンス判定 ===
def is_invidious_instance(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        r = requests.get(url + "/api/v1/stats", headers=headers, timeout=5)
        if r.ok and r.json().get("software") == "invidious":
            return True
    except Exception as e:
        print(f"[無効] {url}: {e}")
    return False

# === 既存の候補URLを読み込み ===
existing_candidates = set()
if CANDIDATE_FILE.exists():
    existing_candidates = set(line.strip() for line in CANDIDATE_FILE.read_text().splitlines())

# === Firestoreから取得して新規候補のみ抽出 ===
new_urls = fetch_candidate_urls()
new_to_add = [url for url in new_urls if url not in existing_candidates]

# === 候補をcandidates.txtに追加 ===
if new_to_add:
    with CANDIDATE_FILE.open("a") as f:
        for url in new_to_add:
            f.write(url + "\n")
    print(f"→ {len(new_to_add)} 件を candidates.txt に追加")
else:
    print("→ 新しい候補はありません")

# === 各URLをInvidiousとして検証してvalid.jsonに登録 ===
for url in new_to_add:
    print(f"[検証] {url} → ", end="")
    if is_invidious_instance(url):
        print("有効")
        for category in valid_urls:
            if url not in valid_urls[category]:
                valid_urls[category].append(url)
    else:
        print("無効")

# === valid.jsonに保存 ===
VALID_FILE.write_text(json.dumps(valid_urls, indent=2, ensure_ascii=False))
print("→ valid.json に保存完了")
