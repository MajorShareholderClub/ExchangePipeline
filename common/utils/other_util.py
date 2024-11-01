from common.setting.properties import (
    KOREA_REAL_TOPIC_NAME,
    ASIA_REAL_TOPIC_NAME,
    NE_REAL_TOPIC_NAME,
)


def market_name_extract(uri: str) -> str:
    """소켓 에서 마켓 이름 추출하는 메서드"""
    # 'wss://' 제거
    uri_parts = uri.split("//")[-1].split(".")

    # 그렇지 않으면 첫 번째 파트를 반환
    return uri_parts[1].upper()


def get_topic_name(location: str) -> str:
    """토픽 이름을 결정하는 로직을 처리"""
    if location.lower() == "korea":
        return f"{KOREA_REAL_TOPIC_NAME}"
    elif location.lower() == "ne":
        return f"{NE_REAL_TOPIC_NAME}"
    return f"{ASIA_REAL_TOPIC_NAME}"
