import requests
import os

URL = "https://firestore.googleapis.com/v1/projects/eviter-api/databases/(default)/documents/invidious_candidates"

def fetch_firestore_candidates():
    try:
        res = requests.get(URL, timeout=10)
        print("Status:", res.status_code)
        print("Response:", res.text)
        if res.status_code == 200:
            data = res.json()
            urls = []
            for doc in data.get("documents", []):
                url = doc["fields"]["url"]["stringValue"]
                urls.append(url)
            return urls
    except Exception as e:
        print("Error:", e)
    return []

def save_to_file(urls, filepath="data/candidates.txt"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        for url in urls:
            f.write(url.strip() + "\n")
    print(f"保存完了: {filepath}")

if __name__ == "__main__":
    urls = fetch_firestore_candidates()
    if urls:
        save_to_file(urls)
    else:
        print("FirestoreからURL取得できませんでした。")
