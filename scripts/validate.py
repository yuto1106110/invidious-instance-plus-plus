
import json, requests
from urllib.parse import urljoin
from pathlib import Path
from fetch_firebase import fetch_from_firebase

CANDIDATE_FILE = Path("candidates/unverified.txt")
VALID_FILE = Path("data/valid.json")
INVALID_FILE = Path("data/invalid.txt")

def is_invidious(url):
    try:
        res = requests.get(urljoin(url, "/api/v1/stats"), timeout=5)
        return res.status_code == 200 and "software" in res.json()
    except:
        return False

# 既存の有効・無効URL
valid_urls = json.loads(VALID_FILE.read_text()) if VALID_FILE.exists() else {
    "video": [],
    "search": [],
    "channel": [],
    "playlist": [],
    "comments": []
}
invalid_urls = set(INVALID_FILE.read_text().splitlines()) if INVALID_FILE.exists() else set()

# 候補の読み込み（既存 + Firebaseから）
raw_candidates = set(CANDIDATE_FILE.read_text().splitlines() if CANDIDATE_FILE.exists() else [])
firebase_urls = fetch_from_firebase()
all_candidates = set(firebase_urls).union(raw_candidates)

# 判定 → invidiousだけ残して再保存
new_candidates = []
new_valid = {
    "video": [],
    "search": [],
    "channel": [],
    "playlist": [],
    "comments": []
}
new_invalid = []

for url in sorted(all_candidates):
    url = url.strip().rstrip("/")
    if not url or url in valid_urls["video"] or url in valid_urls["search"] or url in valid_urls["channel"] or url in valid_urls["playlist"] or url in valid_urls["comments"] or url in invalid_urls:
        continue
    if is_invidious(url):
        print(f"[検証] {url} → Invidious")
        if url not in valid_urls["video"]:
            new_valid["video"].append(url)
        new_candidates.append(url)  # 未検証だがInvidiousと判定
    else:
        print(f"[検証] {url} → 無効")
        new_invalid.append(url)

# 保存
VALID_FILE.write_text(json.dumps(valid_urls | new_valid, indent=2))
INVALID_FILE.write_text("\n".join(sorted(invalid_urls.union(new_invalid))))
CANDIDATE_FILE.write_text("\n".join(sorted(new_candidates)))
