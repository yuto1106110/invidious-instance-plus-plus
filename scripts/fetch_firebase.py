import requests
import os
from pathlib import Path

FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/eviter-api/databases/(default)/documents/invidious_candidates"
OUTPUT_FILE = Path("data/candidates.txt")

def fetch_urls_from_firestore():
    try:
        res = requests.get(FIRESTORE_URL, timeout=5)
        if res.status_code == 200:
            data = res.json()
            urls = []
            for doc in data.get("documents", []):
                fields = doc.get("fields", {})
                if "url" in fields and "stringValue" in fields["url"]:
                    urls.append(fields["url"]["stringValue"])
            return urls
        else:
            print(f"Firestore fetch failed. Status: {res.status_code}")
    except Exception as e:
        print("Firebase fetch error:", e)
    return []

def save_to_file(urls):
    if not urls:
        print("→ URLなし。書き込みスキップ")
        return
    os.makedirs(OUTPUT_FILE.parent, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(urls))
    print(f"→ {OUTPUT_FILE} に保存完了。")

# 実行
urls = fetch_urls_from_firestore()
print("取得URL数:", len(urls))
save_to_file(urls)
