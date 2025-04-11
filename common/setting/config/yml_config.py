import yaml
from pathlib import Path


def get_ticker_format(
    exchange_name: str,
    yml_name: str = "_market_all_ticker.yml",
) -> list[str] | None:
    """
    거래소 이름과 스키마 dict를 받아 해당 거래소의 ticker 포맷을 반환합니다.
    """
    yml_path = Path(__file__).parent / yml_name

    with open(yml_path, "r", encoding="utf-8") as f:
        ticker_schema = yaml.safe_load(f)

    name = exchange_name.lower()
    if name not in ticker_schema:
        raise ValueError(f"지원하지 않는 거래소입니다: {exchange_name}")

    return ticker_schema[name].get("parameter", [])
