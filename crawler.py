import requests
from bs4 import BeautifulSoup
import feedparser
import re
import time
import json

# 保存ファイル名
OUTPUT_FILE = "working_invidious_instances.json"

# ヘッダー（優しいUser-Agent）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; InvidiousCrawler/1.0; +https://example.com/crawler)"
}

# 公式APIから取得
def fetch_from_official_list():
    try:
        res = requests.get("https://api.invidious.io/instances.json", headers=HEADERS, timeout=10)
        instances = res.json()
        urls = []
        for instance in instances:
            if len(instance) >= 2 and isinstance(instance[0], str):
                urls.append(f"https://{instance[0]}")
        print(f"[公式] {len(urls)}個取得")
        return urls
    except Exception as e:
        print("[公式] エラー:", e)
        return []

# GitHubから取得
def fetch_from_github():
    urls = []
    try:
        res = requests.get("https://github.com/iv-org/invidious/wiki/Invidious-Instances", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")
        links = soup.find_all("a", href=True)
        for link in links:
            href = link['href']
            if href.startswith("http") and "invidio" in href:
                urls.append(href)
        print(f"[GitHub] {len(urls)}個取得")
    except Exception as e:
        print("[GitHub] エラー:", e)
    return urls

# redditから取得
def fetch_from_reddit():
    urls = []
    try:
        rss_url = "https://www.reddit.com/r/invidious/.rss"
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            matches = re.findall(r"https?://[^\s\"]+", entry.summary)
            for url in matches:
                if "invidio" in url:
                    urls.append(url)
        print(f"[Reddit] {len(urls)}個取得")
    except Exception as e:
        print("[Reddit] エラー:", e)
    return urls

# 簡易検索（擬似Google/Bingクロール）
def fetch_from_fake_search():
    urls = []
    search_targets = [
        "https://www.google.com/search?q=invidious+instance+list",
        "https://www.google.com/search?q=invidious+public+server",
    ]
    for target in search_targets:
        try:
            res = requests.get(target, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, "lxml")
            links = soup.find_all("a", href=True)
            for link in links:
                href = link['href']
                match = re.search(r"https?://[^\s&]+", href)
                if match:
                    url = match.group()
                    if "invidio" in url:
                        urls.append(url)
        except Exception as e:
            print("[検索] エラー:", e)
    print(f"[検索] {len(urls)}個取得")
    return urls

# 本当にInvidiousかチェック
def check_instance_alive(url):
    try:
        if not url.startswith("http"):
            url = "https://" + url
        stats_url = url.rstrip("/") + "/api/v1/stats"
        res = requests.get(stats_url, headers=HEADERS, timeout=5)
        if res.status_code == 200 and "software" in res.json().get("software", "").lower():
            return True
    except:
        pass
    return False

# 重複除去 + バリデーション
def clean_urls(urls):
    cleaned = set()
    for url in urls:
        if "://" not in url:
            url = "https://" + url
        url = url.rstrip("/")
        cleaned.add(url)
    return list(cleaned)

# メイン処理
def crawl_invidious_instances():
    print("クローリング開始！")
    all_urls = []

    all_urls += fetch_from_official_list()
    all_urls += fetch_from_github()
    all_urls += fetch_from_reddit()
    all_urls += fetch_from_fake_search()

    all_urls = clean_urls(all_urls)
    print(f"収集後、候補数：{len(all_urls)}")

    # 生存確認
    alive_urls = []
    for url in all_urls:
        if check_instance_alive(url):
            print(f"[OK] {url}")
            alive_urls.append(url)
        else:
            print(f"[NG] {url}")

    print(f"最終取得: {len(alive_urls)}個")

    # JSON保存
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(alive_urls, f, ensure_ascii=False, indent=2)

# 5分ごとに実行
def main_loop():
    while True:
        crawl_invidious_instances()
        print("5分休憩...")
        time.sleep(5 * 60)

if __name__ == "__main__":
    crawl_invidious_instances()  # 1回だけ実行して終了する
