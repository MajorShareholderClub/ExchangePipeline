# fmt: off

import yaml
from pathlib import Path

path = Path(__file__).parent.parent


class MarketLoadType:
    def __init__(self, conn_type: str, location: str) -> None:
        self.conn_type = conn_type
        self.location = location

    def load_json(self):
        """
        JSON 파일 로드 (socket 또는 rest)
            - 어떤 가격대를 가지고 올지 파라미터 정의되어 있음
        """
        yml_path = f"{path}/config/{self.location}/_market_{self.conn_type}.yml"
        with open(file=yml_path, mode="r", encoding="utf-8") as file:
            market_info = yaml.safe_load(file)
        
        return market_info
