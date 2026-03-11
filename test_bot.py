import random
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup

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
    print(f"[디버그] 오늘 날짜: {today}")

    url = "https://www.sejong.ac.kr/kor/unilife/cafeteria-info.do"
    params = {"mode": "getMenuList", "cafeCd": "202"}

    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"[계절밥상 API 오류] {e}")
        return []

    available_days = [item.get("startDay") for item in data.get("items", [])]
    print(f"[디버그] API에서 받은 날짜 목록: {available_days}")

    today_item = next(
        (item for item in data.get("items", []) if item.get("startDay") == today),
        None,
    )
    if not today_item:
        print(f"[디버그] 오늘({today}) 날짜 메뉴 없음")
        return []

    html = today_item.get("menuInfo", "")
    soup = BeautifulSoup(html, "html.parser")

    divs = soup.find_all("div", style=lambda s: s and "margin-bottom:10px" in s)
    print(f"[디버그] 파싱된 div 블록 수: {len(divs)}")

    for div in divs:
        label = div.find("span", style=lambda s: s and "E54460" in s)
        if label:
            print(f"[디버그] 발견된 라벨: {label.get_text()}")
        if label and "중식" in label.get_text():
            menu_div = div.find("div", style=lambda s: s and "padding:11px" in s)
            if menu_div:
                raw = menu_div.get_text(separator=" ")
                items = [m.strip() for m in raw.split("·") if m.strip()]
                print(f"[디버그] 중식 메뉴 파싱 성공: {items}")
                return items
            break

    print("[디버그] 중식 블록 파싱 실패")
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

    order = ["산들푸드", "진관키친","계절밥상"]
    picks = []
    for restaurant in order:
        if restaurant in by_restaurant:
            picks.append(random.choice(by_restaurant[restaurant]))

    return picks[:3]


# ─────────────────────────────────────────
# 슬랙 메시지 출력 시뮬레이션
# ─────────────────────────────────────────
def simulate():
    print("=" * 50)
    print("[테스트] 메뉴 풀 구성 중...")
    pool = build_menu_pool()

    by_restaurant = {}
    for item in pool:
        by_restaurant.setdefault(item["restaurant"], 0)
        by_restaurant[item["restaurant"]] += 1
    for r, cnt in by_restaurant.items():
        print(f"[테스트] {r}: {cnt}개")
    print("=" * 50)

    if len(pool) < 3:
        print("메뉴를 불러오는 데 실패했어요 😢 잠시 후 다시 시도해주세요.")
        return

    picks = pick_menus(pool)

    today_str = datetime.now().strftime("%m월 %d일")
    lines = [f"🍱 {today_str} 오늘의 점심 추천 3선!\n"]

    emoji_list = ["1️⃣", "2️⃣", "3️⃣"]
    restaurant_emoji = {"계절밥상": "🥗", "산들푸드": "🍱", "진관키친": "🍜"}

    for i, pick in enumerate(picks):
        r_emoji = restaurant_emoji.get(pick["restaurant"], "🍽️")
        lines.append(f"{emoji_list[i]} {r_emoji} {pick['restaurant']} - {pick['name']}")
        if pick["composition"]:
            chunks = [pick["composition"][j:j+3] for j in range(0, len(pick["composition"]), 3)]
            composition_str = "\n      ".join(" · ".join(chunk) for chunk in chunks)
            lines.append(f"      {composition_str}")

    lines.append("\n맛있는 점심 되세요! 😋")
    print("\n".join(lines))
    print("=" * 50)


if __name__ == "__main__":
    simulate()
