import logging
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# 로깅 설정
# 파일: DEBUG 이상 저장
# 터미널: INFO 이상 출력
# ─────────────────────────────────────────
file_handler = logging.FileHandler("lunch_bot.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, stream_handler])

# ─────────────────────────────────────────
# 환경변수
# ─────────────────────────────────────────
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise ValueError(".env 파일에 SLACK_BOT_TOKEN, SLACK_APP_TOKEN 을 설정해주세요.")

# ─────────────────────────────────────────
# 가격 필터 기준 (원)
# ─────────────────────────────────────────
PRICE_FILTERS = [5000, 6000]
