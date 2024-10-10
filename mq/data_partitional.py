from kafka.partitioner.default import DefaultPartitioner, murmur2

from typing import Optional
import random
import mmh3


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


class ImprovedExchangeDataPartitioner(DefaultPartitioner):
    def __init__(self):
        self.exchange_ids = {
            "upbit": 0,
            "bithumb": 1,
            "coinone": 2,
            "korbit": 3,
            # 해외 거래소 추가
        }
        self.data_type_ids = {"ticker": 0, "orderbook": 1}

    def __call__(
        self, key: Optional[str], all_partitions: list[int], available: list[int]
    ):
        if key is None:
            return super().__call__(key, all_partitions, available)

        try:
            key_str = key.encode("utf-8")  # 문자열을 bytes로 변환
            exchange, data_type, _ = key_str.split("_")
            exchange_id = self.exchange_ids.get(exchange, len(self.exchange_ids))
            data_type_id = self.data_type_ids.get(data_type, 0)

            # 파티션 계산 로직 변경
            partition_count = len(all_partitions)
            exchange_partition_count = (
                partition_count // 2
            )  # 각 데이터 타입당 파티션 수

            base_partition = (exchange_id * 2 + data_type_id) % exchange_partition_count
            final_partition = base_partition + (data_type_id * exchange_partition_count)

            return final_partition % partition_count

        except Exception:
            # 키 형식이 잘못되었거나 예상치 못한 오류 발생 시 기본 파티셔너 사용
            return mmh3.hash(key) % len(all_partitions)
