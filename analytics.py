import logging
import hashlib
import requests
from config import GA4_MEASUREMENT_ID, GA4_API_SECRET

logger = logging.getLogger(__name__)

GA4_URL = "https://www.google-analytics.com/debug/mp/collect"


def anonymize_user_id(user_id: str) -> str:
    """사용자 식별자를 SHA-256으로 익명화"""
    if not user_id:
        user_id = "unknown"

    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()


def send_event(user_id, event_name, params=None):
    logger.info("GA4 함수 진입")

    """GA4로 익명화된 이벤트 전송"""
    if not GA4_MEASUREMENT_ID or not GA4_API_SECRET:
        return

    anonymous_id = anonymize_user_id(user_id)

    payload = {
        "client_id": anonymous_id,
        "events": [{
            "name": event_name,
            "params": params or {}
        }]
    }

    try:
        res = requests.post(
            GA4_URL,
            params={
                "measurement_id": GA4_MEASUREMENT_ID,
                "api_secret": GA4_API_SECRET
            },
            json=payload,
            timeout=3
        )
        logger.debug("GA4 이벤트 전송 - %s (%s)", event_name, res.status_code)
        logger.info("GA4 응답: %s %s", res.status_code, res.text)

    except Exception as e:
        logger.error("GA4 이벤트 전송 실패: %s", e)
