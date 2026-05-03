import logging
import threading
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# 캐시 + Lock
# ─────────────────────────────────────────
_cache = {"date": None, "중식": [], "석식": [], "weekly": {}}
_lock = threading.Lock()


def fetch_gyejeol(meal_type):
    """계절밥상 메뉴 크롤링. meal_type: '중식' or '석식'"""
    today = datetime.now().strftime("%Y-%m-%d")

    with _lock:
        if _cache["date"] == today and meal_type in _cache:
            return _cache[meal_type]

        logger.info("계절밥상 메뉴 크롤링 시작 - %s", today)
        url = "https://www.sejong.ac.kr/kor/unilife/cafeteria-info.do"
        params = {"mode": "getMenuList", "placeId": "1"}

        try:
            res = requests.get(url, params=params, timeout=5)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            logger.error("계절밥상 API 호출 실패: %s", e)
            return []

        items = data.get("items", [])
        _cache["date"] = today

        # 주간 메뉴 캐싱 (중식만)
        weekly = {}
        for item in items:
            if item.get("mealName") == "중식":
                date = item.get("menuDate", "")
                raw = item.get("menuName", "")
                menus = [m.strip() for m in raw.split("·") if m.strip()]
                weekly[date] = menus
        _cache["weekly"] = weekly

        # 중식 / 석식 각각 캐싱
        for mt in ["중식", "석식"]:
            target = next(
                (item for item in items if item.get("menuDate") == today and item.get("mealName") == mt),
                None,
            )
            if target:
                raw = target.get("menuName", "")
                _cache[mt] = [m.strip() for m in raw.split("·") if m.strip()]
                logger.debug("계절밥상 %s 캐싱 완료: %s", mt, _cache[mt])
            else:
                _cache[mt] = []
                logger.warning("계절밥상 오늘(%s) %s 메뉴 없음", today, mt)

        return _cache[meal_type]


def refresh_cache():
    """캐시 초기화 후 재크롤링"""
    with _lock:
        _cache["date"] = None  # 캐시 무효화
    fetch_gyejeol("중식")  # 한 번만 호출해도 중식/석식/주간 전부 캐싱


def get_weekly_cache():
    return _cache.get("weekly", {})