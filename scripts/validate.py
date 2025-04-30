
import json
import requests
from pathlib import Path

# === ディレクトリ・ファイル準備 ===
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

VALID_FILE = data_dir / "valid.json"
CANDIDATE_FILE = data_dir / "candidates.json"

# === 初期形式（全カテゴリ空） ===
base_structure = {
    "video": [],
    "search": [],
    "channel": [],
    "playlist": [],
    "comments": []
}

# === 既存の valid.json を読み込み or 初期化 ===
if VALID_FILE.exists():
    valid_urls = json.loads(VALID_FILE.read_text())
else:
    valid_urls = base_structure.copy()

# === 候補URL読み込み ===
if not CANDIDATE_FILE.exists():
    print("候補URLファイルが見つかりません: data/candidates.json")
    exit(1)

with open(CANDIDATE_FILE, "r") as f:
    candidate_urls = json.load(f)

# === Invidious判定 ===
def is_invidious_instance(url):
    try:
        r = requests.get(url + "/api/v1/stats", timeout=5)
        return r.ok and r.json().get("software") == "invidious"
    except:
        return False

# === 検証・追加 ===
for url in candidate_urls:
    print(f"[検証] {url} → ", end="")
    if is_invidious_instance(url):
        print("Invidious")
        for category in valid_urls.keys():
            if url not in valid_urls[category]:
                valid_urls[category].append(url)
    else:
        print("無効")

# === 保存 ===
VALID_FILE.write_text(json.dumps(valid_urls, indent=2, ensure_ascii=False))
print("→ data/valid.json に保存完了。")
