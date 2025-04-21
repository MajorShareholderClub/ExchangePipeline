import random
from aiokafka.partitioner import DefaultPartitioner, murmur2
from common.logger import PipelineLogger
from common.exceptions import KafkaException

# 로거 설정 - 운영 환경에서는 별도 설정 파일이나 centralized logging 사용 권장
logger = PipelineLogger.get_logger("kafka", "partitional")


class CompositeKeyHashPartitioner(DefaultPartitioner):
    """
    복합 키 기반 해시 파티셔너

    기대하는 키 포맷: "exchange:datatype:symbol"
     - exchange: 거래소 이름 (예: upbit, binance 등)
     - datatype: 데이터 타입 (예: ticker, orderbook 등)
     - symbol: 코인/거래쌍 (예: BTC-KRW, ETH-USDT 등)

    위 포맷에 따라, 키를 정규화한 후 합쳐 composite key를 만들고,
    murmur2 해시 함수를 통해 모든 파티션에 균등하게 분산시키도록 합니다.

    거래소가 삭제되더라도 기존 파티션에 새 키들이 들어오면 재분배되므로,
    파티션 자체에 대한 별도 관리(생성/삭제)가 필요없어집니다.
    """

    @classmethod
    def _decode_key(cls, key: str | None) -> str:
        """키가 bytes일 경우 디코딩하고, None이면 예외 발생."""
        if key is None:
            raise ValueError("유효한 키가 필요합니다 (키가 None 입니다).")
        return key.decode("utf-8") if isinstance(key, bytes) else key

    @classmethod
    def _parse_key(cls, key_str: str) -> tuple[str, str, str]:
        """
        키 문자열을 ':'를 기준으로 분리하여, (exchange, datatype, symbol)을 반환합니다.
        최소한 'exchange:datatype' 형식이어야 하며, symbol은 선택적으로 포함됩니다.
        """
        parts = [p.strip().strip('"') for p in key_str.split(":")]
        if len(parts) < 2:
            raise ValueError(
                f"키 형식 오류: '{key_str}'. 최소 'exchange:datatype' 형식을 필요로 합니다."
            )
        exchange = parts[0]
        datatype = parts[1]
        symbol = parts[2] if len(parts) > 2 else ""
        return exchange, datatype, symbol

    @classmethod
    def _construct_composite_key(cls, exchange: str, datatype: str, symbol: str) -> str:
        """복합 키 구성. symbol이 있으면 포함, 없으면 exchange:datatype 형태로 만듭니다."""
        return f"{exchange}:{datatype}:{symbol}" if symbol else f"{exchange}:{datatype}"

    @classmethod
    def __call__(
        cls, key: str | None, all_partitions: list[int], available: list[int]
    ) -> int:

        try:
            # 1) 키 디코딩 및 정규화
            key_str: str = cls._decode_key(key)
            normalized_key: str = key_str.strip()
            # 2) 키 파싱: exchange, datatype, symbol (symbol은 선택사항)
            exchange, datatype, symbol = cls._parse_key(normalized_key)
            composite_key: str = cls._construct_composite_key(
                exchange, datatype, symbol
            )

            idx: int = murmur2(composite_key.encode("utf-8"))
            idx &= 0x7FFFFFFF
            idx %= len(all_partitions)

            logger.info(f"키 '{normalized_key}' -> 파티션 인덱스: {idx}")
            return all_partitions[idx]
        except KafkaException as e:
            logger.error(f"Partitioning error with key '{key}': {e}")
            return random.choice(all_partitions)
