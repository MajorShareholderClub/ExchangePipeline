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
    # 한국 거래소 파티션 매핑
    KOREA_PARTITION_MAPPING = KoreaPartitionMapping(
        upbit=ExchangeMapping(ticker=0, orderbook=1),
        bithumb=ExchangeMapping(ticker=2, orderbook=3),
        coinone=ExchangeMapping(ticker=4, orderbook=5),
        korbit=ExchangeMapping(ticker=6, orderbook=7),
    )

    # NE 거래소의 파티션 매핑
    NE_PARTITION_MAPPING = ForeignPartitionMapping(
        binance=ExchangeMapping(ticker=0, orderbook=1),
        kraken=ExchangeMapping(ticker=2, orderbook=3),
        coinbase=ExchangeMapping(ticker=4),
    )

    # ASIA 거래소의 파티션 매핑
    ASIA_PARTITION_MAPPING = ForeignPartitionMapping(
        okx=ExchangeMapping(ticker=1, orderbook=2),
        bybit=ExchangeMapping(ticker=3, orderbook=4),
        gateio=ExchangeMapping(ticker=5, orderbook=6),
    )

    @classmethod
    def __call__(cls, key: str, all_partitions: list[int], available: list[int]) -> int:
        try:
            decoded_key = key.decode() if isinstance(key, bytes) else key
            ex_keys = decoded_key.split(":")
            exchange = ex_keys[0].strip('"').lower()
            data_type = ex_keys[1].strip('"').lower()

            match exchange:
                case exchange if exchange in cls.KOREA_PARTITION_MAPPING:
                    partition_mapping = cls.KOREA_PARTITION_MAPPING[exchange]

                case exchange if exchange in cls.NE_PARTITION_MAPPING:
                    partition_mapping = cls.NE_PARTITION_MAPPING[exchange]

                case exchange if exchange in cls.ASIA_PARTITION_MAPPING:
                    partition_mapping = cls.ASIA_PARTITION_MAPPING[exchange]

                case _:
                    raise ValueError(f"Unknown exchange: {exchange}")

            match data_type:
                case "ticker" | "orderbook":
                    partition = partition_mapping[data_type]
                case _:
                    raise ValueError(f"Unknown data type: {data_type}")

            if partition in available:
                return partition
            else:
                # 해당 파티션이 사용 불가능할 경우 fallback
                return available[0]

        except (ValueError, IndexError) as e:
            print(f"파티션 오류 {key}: {e}")
            return random.choice(all_partitions)
        except Exception as e:
            print(f"예외 발생 {key}: {e}")
            return random.choice(all_partitions)
