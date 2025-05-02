import requests
from pathlib import Path

FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/eviter-api/databases/(default)/documents/invidious_candidates"
CANDIDATE_TXT = Path("data/candidates.txt")

def fetch_existing_urls_from_firestore():
    try:
        res = requests.get(FIRESTORE_URL, timeout=5)
        res.raise_for_status()
        documents = res.json().get("documents", [])
        urls = [
            doc["fields"]["url"]["stringValue"]
            for doc in documents
            if "fields" in doc and "url" in doc["fields"]
        ]
        return urls
    except Exception as e:
        print("Firestore fetch error:", e)
        return []

def fetch_existing_urls_from_txt():
    if CANDIDATE_TXT.exists():
        return [line.strip() for line in CANDIDATE_TXT.read_text(encoding="utf-8").splitlines()]
    return []

def add_url_to_firestore(new_url):
    payload = {
        "fields": {
            "url": {"stringValue": new_url}
        }
    }
    try:
        res = requests.post(FIRESTORE_URL, json=payload, timeout=5)
        if res.status_code == 200:
            print(f"[Firestore追加] {new_url}")
        else:
            print(f"[Firestore失敗] {new_url} - {res.status_code}")
    except Exception as e:
        print(f"[Firestoreエラー] {new_url} - {e}")

def append_url_to_txt(new_url):
    with open(CANDIDATE_TXT, "a", encoding="utf-8") as f:
        f.write(new_url + "\n")
    print(f"[TXT追記] {new_url}")

# === ここに新しく追加したいURL ===
new_urls = [
    "https://example-invidious3.com",
    "https://example-invidious4.com"
]

firestore_urls = fetch_existing_urls_from_firestore()
txt_urls = fetch_existing_urls_from_txt()
total_existing = set(firestore_urls + txt_urls)

for url in new_urls:
    if url not in total_existing:
        add_url_to_firestore(url)
        append_url_to_txt(url)
    else:
        print(f"[スキップ] {url}（すでに存在）")
