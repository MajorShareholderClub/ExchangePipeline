from kafka.partitioner.default import DefaultPartitioner, murmur2

from typing import Optional, TypedDict
import random
import mmh3


class ExchangeMapping(TypedDict):
    ticker: int
    orderbook: int


class KoreaPartitionMapping(TypedDict):
    upbit: ExchangeMapping
    bithumb: ExchangeMapping
    coinone: ExchangeMapping
    korbit: ExchangeMapping


class ForeignPartitionMapping(TypedDict):
    binance: ExchangeMapping
    kraken: ExchangeMapping
    okx: ExchangeMapping
    bybit: ExchangeMapping
    gateio: ExchangeMapping


class CoinHashingCustomPartitional(DefaultPartitioner):
    """가상화폐 특정 파티션"""

    @classmethod
    def __call__(
        cls, key: Optional[str], all_partitions: list[int], available: list[int]
    ) -> int:
        """
        Args:
            key (Optional[str]): 파티션에 사용할 키 (가상화폐 이름 등)
            all_partitions (List[int]): 모든 파티션 ID 리스트
            available (List[int]): 사용 가능한 파티션 ID 리스트

        Returns:
            int: 선택된 파티션 ID
        """
        try:
            if key is not None:
                if isinstance(key, str):
                    key = key.encode("utf-8")  # 문자열을 bytes로 변환
                # 키 해싱 하여 파티션 선택
                hashed_key: int = murmur2(key)
                hashed_key &= 0x7FFFFFF

                # hash(key) % 파티션 개수
                partition_idx: int = hashed_key % len(all_partitions)
                print(f"{key} --> {partition_idx}")
                return all_partitions[partition_idx]  # 해싱된 값이 따라서 파티션 적재

            return super().__call__(
                key=key, all_partitions=all_partitions, available=available
            )
        except Exception as e:
            print(f"파티션 오류 {key}: {e}")
            return random.choice(all_partitions)


class CoinSocketDataCustomPartition(DefaultPartitioner):
    KOREA_PARTITION_MAPPING = KoreaPartitionMapping(
        upbit=ExchangeMapping(ticker=0, orderbook=1),
        bithumb=ExchangeMapping(ticker=2, orderbook=3),
        coinone=ExchangeMapping(ticker=4, orderbook=5),
        korbit=ExchangeMapping(ticker=6, orderbook=7),
    )

    FOREIGN_PARTITION_MAPPING = ForeignPartitionMapping(
        binance=ExchangeMapping(ticker=0, orderbook=1),
        kraken=ExchangeMapping(ticker=2, orderbook=3),
        okx=ExchangeMapping(ticker=4, orderbook=5),
        bybit=ExchangeMapping(ticker=6, orderbook=7),
        gateio=ExchangeMapping(ticker=8, orderbook=9),
    )

    @classmethod
    def __call__(cls, key: str, all_partitions: list[int], available: list[int]) -> int:
        try:
            decoded_key = key.decode()
            ex_keys = decoded_key.split(":")
            exchange = ex_keys[0].strip('"').lower()
            data_type = ex_keys[1].strip('"').lower()

            # 한국 거래소 매핑 체크
            if exchange in cls.KOREA_PARTITION_MAPPING:
                partition_mapping = cls.KOREA_PARTITION_MAPPING[exchange]
            # 외국 거래소 매핑 체크
            elif exchange in cls.FOREIGN_PARTITION_MAPPING:
                partition_mapping = cls.FOREIGN_PARTITION_MAPPING[exchange]

            # 데이터 타입에 따른 파티션 선택
            if data_type == "ticker":
                partition = partition_mapping[data_type]
            elif data_type == "orderbook":
                partition = partition_mapping[data_type]
            else:
                raise ValueError(f"Unknown data type: {data_type}")

            # 사용 가능한 파티션 목록 중에서 선택
            if partition in available:
                return partition
            else:
                # 해당 파티션이 사용 불가능할 경우 fallback
                return available[0]

        except Exception as e:
            print(f"파티션 오류 {key}: {e}")
            return random.choice(all_partitions)
