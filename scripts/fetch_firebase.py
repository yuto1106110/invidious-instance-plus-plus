import requests
from pathlib import Path

FIREBASE_URL = "https://eviter-api-default-rtdb.firebaseio.com/candidates.json"
OUTPUT_FILE = Path("data/candidates.txt")

def fetch_from_firebase():
    try:
        res = requests.get(FIREBASE_URL, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return list(set(data.values())) if data else []
    except Exception as e:
        print("Firebase fetch error:", e)
    return []

# === メイン処理 ===
urls = fetch_from_firebase()

if urls:
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url.strip() + "\n")
    print(f"{len(urls)} 件のURLを data/candidates.txt に保存しました。")
else:
    print("FirebaseからURLを取得できませんでした。")
