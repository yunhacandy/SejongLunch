import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

STATS_FILE = "stats.json"


def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # list → set 으로 변환
    return {k: set(v) for k, v in data.items()}


def save_stats(stats):
    # set → list 로 변환 후 저장
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump({k: list(v) for k, v in stats.items()}, f, ensure_ascii=False, indent=2)


def record_user(user_name):
    """유저 접속 기록 - 월별 중복 제거"""
    month = datetime.now().strftime("%Y-%m")
    stats = load_stats()
    stats.setdefault(month, set())
    before = len(stats[month])
    stats[month].add(user_name)
    save_stats(stats)
    # 신규 유저면 로그
    if len(stats[month]) > before:
        logger.debug("신규 MAU 유저 추가 - %s (%s)", user_name, month)
