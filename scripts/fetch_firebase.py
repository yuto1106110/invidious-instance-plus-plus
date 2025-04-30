import requests

FIREBASE_URL = "https://eviter-api-default-rtdb.firebaseio.com/candidates.json"

def fetch_from_firebase():
    try:
        res = requests.get(FIREBASE_URL, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return list(set(data.values())) if data else []
    except Exception as e:
        print("Firebase fetch error:", e)
    return []
