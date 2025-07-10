import random
from aiokafka.partitioner import DefaultPartitioner, murmur2


class CompositeKeyHashPartitioner(DefaultPartitioner):
    """
    복합 키 기반 해시 파티셔너

    기대하는 키 포맷: "exchange:datatype:symbol"
     - exchange: 거래소 이름 (예: upbit, binance 등)
     - datatype: 데이터 타입 (예: ticker, orderbook 등)
     - symbol: 코인/거래쌍 (예: BTC-KRW, ETH-USDT 등)

    위 포맷에 따라 composite key를 구성하고,
    murmur2 해시 함수를 통해 파티션을 결정합니다.
    """

    def __call__(
        self, key: bytes | str | None, all_partitions: list[int], available: list[int]
    ) -> int:
        try:
            # 1. 키 정규화
            key_str = self._decode_key(key)
            exchange, datatype, symbol = self._parse_key(key_str)
            composite_key = self._construct_composite_key(exchange, datatype, symbol)

            # 2. 해시 계산
            idx = murmur2(composite_key.encode("utf-8")) & 0x7FFFFFFF
            partition = all_partitions[idx % len(all_partitions)]
            return partition

        except Exception as e:
            # 예외 발생 시 fallback - 무작위 파티션
            # 실무에선 logger.warning(...) 등 로그 기록 추천
            return random.choice(all_partitions)

    @staticmethod
    def _decode_key(key: bytes | str | None) -> str:
        if key is None:
            raise ValueError("Kafka 메시지에 유효한 Key가 없습니다.")
        return key.decode("utf-8") if isinstance(key, bytes) else str(key)

    @staticmethod
    def _parse_key(key_str: str) -> tuple[str, str, str]:
        parts = [p.strip().strip('"') for p in key_str.split(":")]
        if len(parts) < 2:
            raise ValueError(
                f"키 형식 오류: '{key_str}' (최소 'exchange:datatype' 필요)"
            )
        exchange = parts[0]
        datatype = parts[1]
        symbol = parts[2] if len(parts) > 2 else ""
        return exchange, datatype, symbol

    @staticmethod
    def _construct_composite_key(exchange: str, datatype: str, symbol: str) -> str:
        return f"{exchange}:{datatype}:{symbol}" if symbol else f"{exchange}:{datatype}"
