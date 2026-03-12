import logging
import os
import random
import json
import requests
import ssl
import schedule
import time
import threading
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

ssl._create_default_https_context = ssl.create_default_context
load_dotenv()

# ─────────────────────────────────────────
# 로깅 설정
# ─────────────────────────────────────────
file_handler = logging.FileHandler("lunch_bot.log")
file_handler.setLevel(logging.WARNING)  # 파일엔 WARNING 이상만 저장
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)   # 터미널엔 INFO 이상 출력
stream_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

logging.basicConfig(level=logging.INFO, handlers=[file_handler, stream_handler])
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# 2일 지난 로그 자동 삭제 (매일 자정)
# ─────────────────────────────────────────
def cleanup_old_logs():
    log_file = "lunch_bot.log"
    if not os.path.exists(log_file):
        return

    cutoff = datetime.now() - timedelta(days=7)
    kept_lines = []

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                # 로그 맨 앞의 날짜 파싱
                log_date = datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S")
                if log_date >= cutoff:
                    kept_lines.append(line)
            except ValueError:
                kept_lines.append(line)  # 날짜 파싱 실패한 줄은 유지

    with open(log_file, "w", encoding="utf-8") as f:
        f.writelines(kept_lines)

    logger.info("로그 정리 완료 - %s 이전 로그 삭제", cutoff.strftime("%Y-%m-%d"))


def schedule_cleanup():
    schedule.every().day.at("00:00").do(cleanup_old_logs)
    while True:
        schedule.run_pending()
        time.sleep(60)

# ─────────────────────────────────────────
# Slack 앱 초기화
# ─────────────────────────────────────────
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# ─────────────────────────────────────────
# 고정 메뉴 로드 (menus.json)
# ─────────────────────────────────────────
with open("menus.json", "r", encoding="utf-8") as f:
    FIXED_MENUS = json.load(f)

# ─────────────────────────────────────────
# 계절밥상 오늘 중식 메뉴 크롤링
# ─────────────────────────────────────────
def fetch_gyejeol_lunch():
    today = datetime.now().strftime("%Y%m%d")
    url = "https://www.sejong.ac.kr/kor/unilife/cafeteria-info.do"
    params = {"mode": "getMenuList", "cafeCd": "202"}

    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"[계절밥상 API 오류] {e}")
        return []

    today_item = next(
        (item for item in data.get("items", []) if item.get("startDay") == today),
        None,
    )
    if not today_item:
        return []

    html = today_item.get("menuInfo", "")
    soup = BeautifulSoup(html, "html.parser")

    divs = soup.find_all("div", style=lambda s: s and "margin-bottom:10px" in s)
    for div in divs:
        label = div.find("span", style=lambda s: s and "E54460" in s)
        if label and "중식" in label.get_text():
            menu_div = div.find("div", style=lambda s: s and "padding:11px" in s)
            if menu_div:
                raw = menu_div.get_text(separator=" ")
                items = [m.strip() for m in raw.split("·") if m.strip()]
                return items
            break

    return []

# ─────────────────────────────────────────
# 전체 메뉴 풀 구성
# ─────────────────────────────────────────
def build_menu_pool():
    pool = []

    for item in FIXED_MENUS.get("산들푸드", []):
        price_str = f" ({item['price']:,}원)" if item.get("price") else ""
        pool.append({
            "restaurant": "산들푸드",
            "name": item["name"] + price_str,
            "composition": None,
        })

    for item in FIXED_MENUS.get("진관키친", []):
        price_str = f" ({item['price']:,}원)" if item.get("price") else ""
        pool.append({
            "restaurant": "진관키친",
            "name": item["name"] + price_str,
            "composition": None,
        })

    gyejeol_items = fetch_gyejeol_lunch()
    if gyejeol_items:
        pool.append({
            "restaurant": "계절밥상",
            "name": "중식 (7,000원)",
            "composition": gyejeol_items,
        })

    return pool

# ─────────────────────────────────────────
# 식당별로 각 1개씩, 고정 순서로 추천
# ─────────────────────────────────────────
def pick_menus(pool):
    by_restaurant = {}
    for item in pool:
        by_restaurant.setdefault(item["restaurant"], []).append(item)

    order = ["산들푸드", "진관키친", "계절밥상"]
    picks = []
    for restaurant in order:
        if restaurant in by_restaurant:
            picks.append(random.choice(by_restaurant[restaurant]))

    return picks[:3]

# ─────────────────────────────────────────
# /학식 슬래시 커맨드
# ─────────────────────────────────────────
@app.command("/학식")
def handle_lunch(ack, respond):
    ack()

    pool = build_menu_pool()

    # 계절밥상 없어도 2개 식당으로 추천
    if len(pool) == 0:
        logger.error("메뉴 풀이 비어있음")
        respond("메뉴를 불러오는 데 실패했어요 😢 잠시 후 다시 시도해주세요.")
        return

    picks = pick_menus(pool)
    logger.info("추천 메뉴: %s", [p["name"] for p in picks])

    today_str = datetime.now().strftime("%m월 %d일")
    lines = [f"🍱 *{today_str} 오늘의 점심 추천 3선!*\n"]

    emoji_list = ["1️⃣", "2️⃣", "3️⃣"]
    restaurant_emoji = {"계절밥상": "🥗", "산들푸드": "🍱", "진관키친": "🍜"}

    for i, pick in enumerate(picks):
        r_emoji = restaurant_emoji.get(pick["restaurant"], "🍽️")
        lines.append(f"{emoji_list[i]} {r_emoji} *{pick['restaurant']}* - {pick['name']}")
        if pick["composition"]:
            chunks = [pick["composition"][j:j+3] for j in range(0, len(pick["composition"]), 3)]
            composition_str = "\n      ".join(" · ".join(chunk) for chunk in chunks)
            lines.append(f"      _{composition_str}_")

    # 계절밥상 없는 날 안내
    if not any(p["restaurant"] == "계절밥상" for p in picks):
        lines.append("\n_※ 오늘은 계절밥상 메뉴가 없어요._")

    lines.append("\n맛있는 점심 되세요! 😋")
    respond("\n".join(lines))

# ─────────────────────────────────────────
# 앱 실행
# ─────────────────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=schedule_cleanup, daemon=True).start()
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
