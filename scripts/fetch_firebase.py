import requests

FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/eviter-api/databases/(default)/documents/invidious_candidates"

def fetch_urls_from_firestore():
    try:
        res = requests.get(FIRESTORE_URL, timeout=5)
        if res.status_code == 200:
            data = res.json()
            urls = []
            for doc in data.get("documents", []):
                url_value = doc["fields"]["url"]["stringValue"]
                urls.append(url_value)
            return urls
        else:
            print("Error:", res.status_code, res.text)
    except Exception as e:
        print("Fetch error:", e)
    return []

# 書き込み
urls = fetch_urls_from_firestore()
if urls:
    with open("data/candidates.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(urls))
