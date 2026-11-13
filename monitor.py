
import os
import json
import re
import sys
import requests
from bs4 import BeautifulSoup
from pathlib import Path

PRODUCTS = {
    "OUR WISH Scrunchie": {
        "id": "27705",
        "url": "https://smtownandstore.com/product/2025-nct-wish-1st-concert-tour-into-the-wish-our-wish-scrunchie/27705/category/53/"
    },
    "LOG IN Fanlight Key Ring": {
        "id": "26098",
        "url": "https://smtownandstore.com/product/nct-wish-asia-tour-log-in-fanlight-key-ring/26098/category/53/"
    }
}

WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]
USER_ID = os.environ["DISCORD_USER_ID"]
STATE_FILE = Path("state.json")

def send_discord(title, description, url=None):
    payload = {
        "content": f"<@{USER_ID}>",
        "allowed_mentions": {
            "parse": [],
            "users": [USER_ID]
        },
        "embeds": [{
            "title": title,
            "description": description,
            "color": 5763719,
            **({"url": url} if url else {})
        }]
    }

    response = requests.post(
        WEBHOOK,
        json=payload,
        timeout=20
    )
    response.raise_for_status()


def check_stock(product):
    response = requests.get(
        product["url"],
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "ko-KR,ko;q=0.9"
        },
        timeout=25
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    if product["id"] not in response.url:
        return "unknown"

    # 상품 구매 영역에서 SOLD OUT 요소 찾기
    area = soup.select_one(".xans-product-action")
    if not area:
        return "unknown"

    sold_out = area.select_one("span.sold_out")
    if not sold_out:
        return "unknown"

    classes = sold_out.get("class", [])

    if "displaynone" in classes:
        return "in_stock"

    return "sold_out"


def main():
    if "--test" in sys.argv:
        send_discord(
            "💚 NCT WISH 알림 테스트 성공!",
            "Discord 멘션 및 푸시 알림 테스트입니다."
        )
        print("Discord test message sent!")
        return

    if STATE_FILE.exists():
        state = json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )
    else:
        state = {}

    failed = False

    for name, product in PRODUCTS.items():
        try:
            current = check_stock(product)
            previous = state.get(name)

            print(f"{name}: {previous} -> {current}")

            if current == "unknown":
                print("Stock status uncertain; skipped.")
                continue

            if current == "in_stock" and previous != "in_stock":
                send_discord(
                    "💚 NCT WISH 재입고 감지!",
                    f"**{name}**\n구매 가능 상태가 감지되었습니다. 상품 페이지를 확인하세요!",
                    product["url"]
                )

            state[name] = current

        except Exception as error:
            print(f"ERROR checking {name}: {error}")
            failed = True

    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    if failed:
        sys.exit(1)

if __name__ == "__main__":
    main()
