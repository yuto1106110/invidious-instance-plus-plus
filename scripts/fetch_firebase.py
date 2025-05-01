import requests
from pathlib import Path

# Firestore REST APIエンドポイント（自分のプロジェクトIDに変更）
PROJECT_ID = "eviter-api"
COLLECTION = "invidious_candidates"
URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{COLLECTION}"

OUTPUT_FILE = Path("data/candidates.txt")

def fetch_from_firestore():
    try:
        res = requests.get(URL, timeout=5)
        if res.status_code == 200:
            data = res.json()
            urls = []
            for doc in data.get("documents", []):
                url_field = doc["fields"].get("url", {}).get("stringValue")
                if url_field:
                    urls.append(url_field)
            return urls
        else:
            print("Firestore API error:", res.status_code, res.text)
    except Exception as e:
        print("Fetch error:", e)
    return []

# === 実行・保存 ===
urls = fetch_from_firestore()

if urls:
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url.strip() + "\n")
    print(f"{len(urls)} 件のURLを data/candidates.txt に保存しました。")
else:
    print("FirestoreからURLを取得できませんでした。")
