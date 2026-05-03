from datetime import datetime

from config import PRICE_FILTERS
from crawler import fetch_gyejeol, get_weekly_cache
from menus import get_fixed_menus

FEEDBACK_URL = "https://forms.gle/XncXnQb3pBDw2YYF9"


def build_main_menu_blocks(menus=None):
    """계절밥상 중식을 기본으로 표시하고 하단에 버튼 배치.
    menus를 외부에서 넘기면 재호출 없이 사용 (이중 호출 방지)
    """
    if menus is None:
        menus = fetch_gyejeol("중식")

    today_str = datetime.now().strftime("%m월 %d일")

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"🥗 *계절밥상 - {today_str} 중식* (7,000원)"}},
        {"type": "divider"},
    ]

    if menus:
        menu_str = "\n".join([f"- {m}" for m in menus])
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": menu_str}})
    else:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "오늘 계절밥상 중식 메뉴가 홈페이지에 없어요 😢"}})

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "actions",
        "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "🎲 메뉴 랜덤 추천"}, "action_id": "random_recommend"},
            {"type": "button", "text": {"type": "plain_text", "text": "🌙 계절밥상 석식"}, "action_id": "show_gyejeol_dinner"},
            {"type": "button", "text": {"type": "plain_text", "text": "📅 계절밥상 주간메뉴"}, "action_id": "show_weekly"},
        ]
    })
    blocks.append({
        "type": "actions",
        "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "🍱 산들푸드"}, "action_id": "show_sandle"},
            {"type": "button", "text": {"type": "plain_text", "text": "🍜 진관키친"}, "action_id": "show_jingwan"},
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "📝 의견 주기"},
                "url": FEEDBACK_URL,
                "action_id": "feedback",
            },
        ]
    })
    return blocks


def build_random_blocks(result):
    today = datetime.now().strftime("%m월 %d일")
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"🍱 *{today} 오늘의 점심 추천!*"}},
        {"type": "divider"},
    ]

    for r, emoji in [("산들푸드", "🍱"), ("진관키친", "🍜")]:
        if r in result:
            menu_lines = "\n".join([f"- {m['name']}" for m in result[r]])
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"{emoji} *{r}*\n{menu_lines}"}})

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "※ 메뉴 구성 및 가격은 실제와 다를 수 있어요.\n맛있는 점심 되세요! 😋"}})
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "actions",
        "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "🔄 다시 추천"}, "action_id": "random_recommend"},
            {"type": "button", "text": {"type": "plain_text", "text": "⬅️ 처음으로"}, "action_id": "back_to_main"},
        ]
    })
    return blocks


def build_gyejeol_blocks(meal_type):
    menus = fetch_gyejeol(meal_type)
    today_str = datetime.now().strftime("%m월 %d일")
    emoji = "🥗" if meal_type == "중식" else "🌙"
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"{emoji} *계절밥상 - {today_str} {meal_type}* (7,000원)"}},
        {"type": "divider"},
    ]
    if menus:
        menu_str = "\n".join([f"- {m}" for m in menus])
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": menu_str}})
    else:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"오늘 계절밥상 {meal_type} 메뉴가 홈페이지에 없어요 😢"}})
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "actions",
        "elements": [{"type": "button", "text": {"type": "plain_text", "text": "⬅️ 처음으로"}, "action_id": "back_to_main"}]
    })
    return blocks


def build_restaurant_blocks(restaurant_key, emoji, label, price_filter=None):
    fixed_menus = get_fixed_menus()
    menus = fixed_menus.get(restaurant_key, [])
    if price_filter:
        menus = [m for m in menus if m.get("price") and m["price"] <= price_filter]

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"{emoji} *{label} 전체 메뉴*" + (f" ({price_filter:,}원 이하)" if price_filter else "")}},
        {"type": "divider"},
    ]

    if menus:
        menu_lines = "\n".join([
            f"- {m['name']} ({m['price']:,}원)" if m.get("price") else f"- {m['name']}"
            for m in menus
        ])
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": menu_lines}})
    else:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "해당 조건의 메뉴가 없어요 😢"}})

    blocks.append({"type": "divider"})
    filter_action = "filter_sandle" if restaurant_key == "산들푸드" else "filter_jingwan"
    show_action = "show_sandle" if restaurant_key == "산들푸드" else "show_jingwan"

    filter_buttons = [
        {"type": "button", "text": {"type": "plain_text", "text": f"{p:,}원 이하"}, "action_id": f"{filter_action}_{p}"}
        for p in PRICE_FILTERS
    ]
    filter_buttons += [
        {"type": "button", "text": {"type": "plain_text", "text": "전체보기"}, "action_id": show_action},
        {"type": "button", "text": {"type": "plain_text", "text": "⬅️ 처음으로"}, "action_id": "back_to_main"},
    ]
    blocks.append({"type": "actions", "elements": filter_buttons})
    return blocks


def build_weekly_blocks():
    fetch_gyejeol("중식")  # 캐시 갱신
    weekly = get_weekly_cache()
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": "📅 *계절밥상 이번 주 중식 메뉴* (7,000원)"}},
        {"type": "divider"},
    ]
    if not weekly:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "이번 주 메뉴 정보가 없어요 😢"}})
    else:
        for date in sorted(weekly.keys()):
            menus = weekly[date]
            try:
                dt = datetime.strptime(date, "%Y-%m-%d")
                day_str = dt.strftime("%m/%d") + f" ({['월','화','수','목','금','토','일'][dt.weekday()]})"
            except Exception:
                day_str = date
            menu_str = "\n".join([f"- {m}" for m in menus])
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*{day_str}*\n{menu_str}"}})
            blocks.append({"type": "divider"})

    blocks.append({
        "type": "actions",
        "elements": [{"type": "button", "text": {"type": "plain_text", "text": "⬅️ 처음으로"}, "action_id": "back_to_main"}]
    })
    return blocks
