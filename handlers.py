import logging

from config import PRICE_FILTERS
from blocks import (
    build_main_menu_blocks,
    build_random_blocks,
    build_gyejeol_blocks,
    build_restaurant_blocks,
    build_weekly_blocks,
)
from crawler import fetch_gyejeol
from menus import build_menu_pool, pick_menus
from stats import record_user

logger = logging.getLogger(__name__)


def register_handlers(app):

    # ─────────────────────────────────────────
    # /학식 슬래시 커맨드
    # ─────────────────────────────────────────
    @app.command("/학식")
    def handle_lunch(ack, respond, body):
        ack()
        user_name = body.get("user_name", "unknown")
        menus = fetch_gyejeol("중식")  # 한 번만 호출 후 blocks에 넘김
        logger.info("/학식 요청 - 유저: %s (계절밥상 중식 %s)", user_name,
                    "캐시" if menus else "메뉴없음")
        record_user(user_name)
        respond(blocks=build_main_menu_blocks(menus=menus), text="학식 메뉴")

    # ─────────────────────────────────────────
    # 버튼 액션 핸들러
    # ─────────────────────────────────────────
    @app.action("random_recommend")
    def action_random(ack, respond, body):
        ack()
        user_name = body.get("user", {}).get("username", "unknown")
        logger.info("랜덤 추천 요청 - 유저: %s", user_name)
        pool = build_menu_pool()
        if not pool:
            respond(text="메뉴를 불러오는 데 실패했어요 😢 잠시 후 다시 시도해주세요.")
            return
        result = pick_menus(pool)
        respond(blocks=build_random_blocks(result), text="랜덤 추천")

    @app.action("back_to_main")
    def action_back(ack, respond, body):
        ack()
        user_name = body.get("user", {}).get("username", "unknown")
        logger.info("처음으로 - 유저: %s", user_name)
        menus = fetch_gyejeol("중식")  # 한 번만 호출 후 blocks에 넘김
        respond(blocks=build_main_menu_blocks(menus=menus), text="학식 메뉴")

    @app.action("show_gyejeol_dinner")
    def action_gyejeol_dinner(ack, respond, body):
        ack()
        user_name = body.get("user", {}).get("username", "unknown")
        logger.info("계절밥상 석식 조회 - 유저: %s", user_name)
        respond(blocks=build_gyejeol_blocks("석식"), text="계절밥상 석식")

    @app.action("show_sandle")
    def action_sandle(ack, respond, body):
        ack()
        user_name = body.get("user", {}).get("username", "unknown")
        logger.info("산들푸드 조회 - 유저: %s", user_name)
        respond(blocks=build_restaurant_blocks("산들푸드", "🍱", "산들푸드"), text="산들푸드 메뉴")

    @app.action("show_jingwan")
    def action_jingwan(ack, respond, body):
        ack()
        user_name = body.get("user", {}).get("username", "unknown")
        logger.info("진관키친 조회 - 유저: %s", user_name)
        respond(blocks=build_restaurant_blocks("진관키친", "🍜", "진관키친"), text="진관키친 메뉴")

    @app.action("show_weekly")
    def action_weekly(ack, respond, body):
        ack()
        user_name = body.get("user", {}).get("username", "unknown")
        logger.info("주간메뉴 조회 - 유저: %s", user_name)
        respond(blocks=build_weekly_blocks(), text="주간 메뉴")

    @app.action("feedback")
    def action_feedback(ack):
        ack()

    # PRICE_FILTERS 기반으로 동적 핸들러 등록
    for price in PRICE_FILTERS:
        for restaurant_key, emoji, label, prefix in [
            ("산들푸드", "🍱", "산들푸드", "filter_sandle"),
            ("진관키친", "🍜", "진관키친", "filter_jingwan"),
        ]:
            action_id = f"{prefix}_{price}"

            def make_handler(rk=restaurant_key, em=emoji, lb=label, pf=price):
                def handler(ack, respond):
                    ack()
                    respond(
                        blocks=build_restaurant_blocks(rk, em, lb, price_filter=pf),
                        text=f"{lb} {pf:,}원 이하"
                    )
                return handler

            app.action(action_id)(make_handler())
