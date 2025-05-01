import json
import requests
from pathlib import Path

# === ディレクトリ・ファイル準備 ===
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

VALID_FILE = data_dir / "valid.json"
CANDIDATE_FILE = data_dir / "candidates.txt"

# === 初期形式（全カテゴリ空） ===
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

# === 候補URL読み込み（テキスト形式：1行1URL） ===
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
