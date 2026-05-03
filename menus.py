import json
import logging
import random

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# 고정 메뉴 로드
# ─────────────────────────────────────────
with open("menus.json", "r", encoding="utf-8") as f:
    FIXED_MENUS = json.load(f)

# 메뉴 풀 캐시 (한 번만 생성)
_pool_cache = None


def build_menu_pool():
    """산들푸드 + 진관키친 메뉴 풀 (최초 1회만 생성 후 캐싱)"""
    global _pool_cache
    if _pool_cache is not None:
        return _pool_cache

    pool = []
    for item in FIXED_MENUS.get("산들푸드", []):
        price_str = f" ({item['price']:,}원)" if item.get("price") else ""
        pool.append({"restaurant": "산들푸드", "name": item["name"] + price_str})
    for item in FIXED_MENUS.get("진관키친", []):
        price_str = f" ({item['price']:,}원)" if item.get("price") else ""
        pool.append({"restaurant": "진관키친", "name": item["name"] + price_str})

    _pool_cache = pool
    logger.debug("메뉴 풀 캐싱 완료 - 총 %d개", len(_pool_cache))
    return _pool_cache


def pick_menus(pool):
    by_restaurant = {}
    for item in pool:
        by_restaurant.setdefault(item["restaurant"], []).append(item)

    result = {}
    for restaurant in ["산들푸드", "진관키친"]:
        menus = by_restaurant.get(restaurant, [])
        result[restaurant] = random.sample(menus, min(3, len(menus)))

    return result


def get_fixed_menus():
    return FIXED_MENUS
