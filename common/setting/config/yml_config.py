import yaml
from pathlib import Path
from functools import lru_cache


base_path: str = Path(__file__).parent
ticker_path: str = base_path / "_market_all_ticker.yml"
template_path: str = base_path / "_socket_all_parameter.yml"


@lru_cache(maxsize=30)
def load_yml_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class YmlConfig:
    def __init__(self, yml_path: str) -> None:
        self.yml_path = yml_path

    def load(self) -> dict:
        # 실제로는 이미 캐싱된 load_yml_file을 호출하므로
        # I/O는 한 번만 일어나게 됨
        return load_yml_file(self.yml_path)

    def get_ticker_format(self, exchange_name: str) -> list[str] | None:
        ticker_schema = self.load()
        name = exchange_name.lower()
        if name not in ticker_schema:
            raise ValueError(f"지원하지 않는 거래소입니다: {exchange_name}")
        return ticker_schema[name].get("parameter", [])

    def load_templates_from_yaml(self) -> dict:
        return self.load()


ticker_config = YmlConfig(ticker_path).get_ticker_format
template_config = YmlConfig(template_path).load_templates_from_yaml
