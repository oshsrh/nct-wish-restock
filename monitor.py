
import os
import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path

PRODUCTS = {
    "OUR WISH Scrunchie":
        "https://smtownandstore.com/product/2025-nct-wish-1st-concert-tour-into-the-wish-our-wish-scrunchie/27705/category/53/",
    "LOG IN Fanlight Key Ring":
        "https://smtownandstore.com/product/nct-wish-asia-tour-log-in-fanlight-key-ring/26098/category/53/"
}

WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]
USER_ID = os.environ["DISCORD_USER_ID"]
STATE_FILE = Path("state.json")

def check_stock(url):
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    # 보수적 판별: 모호한 경우 알림을 보내지 않음
    sold_out = bool(re.search(r"sold\s*out|품절", text))
    return "sold_out" if sold_out else "unknown"

def notify(name, url):
    message = {
        "content": f"<@{USER_ID}> 💚 **NCT WISH 재입고 감지!**",
        "embeds": [{
            "title": name,
            "description": "상품이 구매 가능한 상태로 변경되었습니다!",
            "url": url,
            "color": 5763719
        }],
        "allowed_mentions": {
            "parse": [],
            "users": [USER_ID]
        }
    }
    r = requests.post(WEBHOOK, json=message, timeout=20)
    r.raise_for_status()

def main():
    state = {}
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())

    for name, url in PRODUCTS.items():
        current = check_stock(url)
        previous = state.get(name)

        print(f"{name}: {previous} -> {current}")

        if previous == "sold_out" and current == "in_stock":
            notify(name, url)

        if current != "unknown":
            state[name] = current

    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2)
    )

if __name__ == "__main__":
    main()
