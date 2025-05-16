import json
import requests
import time
from pathlib import Path

# === パス設定 ===
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
VALID_FILE = data_dir / "valid.json"
CANDIDATE_FILE = data_dir / "candidates.txt"

# === 空の構造（全カテゴリ用） ===
base_structure = {
    "video": [],
    "search": [],
    "channel": [],
    "playlist": [],
    "comments": []
}

# === valid.json 読み込み ===
if VALID_FILE.exists():
    try:
        valid_urls = json.loads(VALID_FILE.read_text())
    except:
        valid_urls = base_structure.copy()
else:
    valid_urls = base_structure.copy()

# === Firestore から候補を取得して candidates.txt に追加 ===
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

# === Invidiousかどうかチェック ===
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
    return False

# === レスポンス時間付きのリクエスト
def timed_request(full_url):
    try:
        start = time.time()
        res = requests.get(full_url, timeout=7)
        duration = time.time() - start
        return res, duration
    except:
        return None, float('inf')

# === video/comments 両方OKかつ速いものを上位3件選出
def validate_top3_instances(urls):
    results = []
    for url in urls:
        print(f"[検証中] {url}")

        if not is_invidious(url):
            print("  → Invidiousではありません（除外）")
            continue

        c_url = url.rstrip("/") + "/api/v1/comments/RgKAFK5djSk"
        v_url = url.rstrip("/") + "/api/v1/videos/RgKAFK5djSk"

        rc, t1 = timed_request(c_url)
        rv, t2 = timed_request(v_url)

        if not rc or not rv:
            print("  → 応答なし")
            continue

        try:
            c_json = rc.json()
            v_json = rv.json()
        except:
            print("  → JSON不正")
            continue

        if not ("comments" in c_json and len(c_json["comments"]) > 0):
            print("  → コメントなし")
            continue

        if not ("title" in v_json and (
            "hlsUrl" in v_json or
            any("url" in s for s in v_json.get("formatStreams", [])) or
            any("url" in s for s in v_json.get("adaptiveFormats", []))
        )):
            print("  → 動画取得不可")
            continue

        avg_time = (t1 + t2) / 2
        print(f"  → OK (avg: {avg_time:.2f}s)")
        results.append((url, avg_time))

    results.sort(key=lambda x: x[1])
    return [x[0] for x in results[:3]]

# === 最終検証＆保存
def validate_candidates():
    if not CANDIDATE_FILE.exists():
        print("candidates.txt が存在しません。")
        return

    urls = [line.strip() for line in CANDIDATE_FILE.read_text().splitlines() if line.strip()]
    top3 = validate_top3_instances(urls)

    if not top3:
        print("有効なインスタンスが見つかりませんでした。")
        return

    print(f"\n=== 採用されたインスタンス (最大3件) ===")
    for u in top3:
        print(f"  → {u}")

    new_valid = {k: top3.copy() for k in base_structure}
    json_text = json.dumps(new_valid, indent=2, ensure_ascii=False).replace('"', "'")
    VALID_FILE.write_text(json_text, encoding="utf-8")
    print("\n→ valid.json に保存しました。")

# === 実行 ===
fetch_from_firestore_and_update_candidates()
validate_candidates()
