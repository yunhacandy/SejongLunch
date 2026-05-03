import ssl
import schedule
import time
import threading
from datetime import datetime, timedelta
import logging

import config  # 로깅 + 환경변수 초기화
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from handlers import register_handlers
from crawler import refresh_cache, get_weekly_cache

ssl._create_default_https_context = ssl.create_default_context

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# Slack 앱 초기화
# ─────────────────────────────────────────
app = App(token=config.SLACK_BOT_TOKEN)
register_handlers(app)


# ─────────────────────────────────────────
# 7일 지난 로그 자동 삭제
# ─────────────────────────────────────────
def cleanup_old_logs():
    log_file = "lunch_bot.log"
    import os
    if not os.path.exists(log_file):
        return
    cutoff = datetime.now() - timedelta(days=7)
    kept_lines = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                log_date = datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S")
                if log_date >= cutoff:
                    kept_lines.append(line)
            except ValueError:
                kept_lines.append(line)
    with open(log_file, "w", encoding="utf-8") as f:
        f.writelines(kept_lines)
    logger.info("로그 정리 완료 - %s 이전 로그 삭제", cutoff.strftime("%Y-%m-%d"))


# ─────────────────────────────────────────
# 주간메뉴 없으면 재시도
# ─────────────────────────────────────────
def refresh_if_no_weekly():
    weekly = get_weekly_cache()
    today = datetime.now().strftime("%Y-%m-%d")
    # 주간메뉴가 없거나 이번 주 이후 데이터가 없으면 재크롤링
    if not weekly or not any(date >= today for date in weekly.keys()):
        logger.info("주간메뉴 없음 - 재크롤링 시도")
        refresh_cache()
    else:
        logger.debug("주간메뉴 이미 캐시됨 - 스킵")


# ─────────────────────────────────────────
# 스케줄 등록
# ─────────────────────────────────────────
def schedule_jobs():
    # 로그 정리 + 캐시 갱신 - 매일 자정
    schedule.every().day.at("00:00").do(cleanup_old_logs)
    schedule.every().day.at("00:00").do(refresh_cache)

    # 월요일 집중 시도 (주간메뉴 없으면 재시도)
    schedule.every().monday.at("06:00").do(refresh_if_no_weekly)
    schedule.every().monday.at("07:00").do(refresh_if_no_weekly)
    schedule.every().monday.at("08:00").do(refresh_if_no_weekly)
    schedule.every().monday.at("09:00").do(refresh_if_no_weekly)

    while True:
        schedule.run_pending()
        time.sleep(60)


# ─────────────────────────────────────────
# 앱 실행
# ─────────────────────────────────────────
if __name__ == "__main__":
    # 시작 시 미리 크롤링
    refresh_cache()

    threading.Thread(target=schedule_jobs, daemon=True).start()
    logger.info("슬랙봇 시작")
    handler = SocketModeHandler(app, config.SLACK_APP_TOKEN)
    handler.start()