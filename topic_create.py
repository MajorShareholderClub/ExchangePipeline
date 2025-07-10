from messaging.data_admin import new_topic_initialization, delete_all_topics


def data_sending_start() -> None:
    """
    거래소 기반 파티셔닝을 위한 토픽 생성

    각 지역별로 파티션 수를 조정하여 거래소 데이터가 파티션에 효율적으로 분산되도록 구성:
    - Korea: 주요 거래소(Upbit, Bithumb 등)를 고려하여 6개 파티션
    - Asia: 주요 거래소(Binance Asia, OKX 등)를 고려하여 4개 파티션
    - NE: 주요 거래소(Binance US, Coinbase 등)를 고려하여 4개 파티션

    토픽 형식: {region}_{request_type}
    - 지역과 데이터 타입으로 구분된 간단한 토픽 구조 유지
    """
    try:
        # 토픽 목록 (지역 및 데이터 타입별)
        topic = [
            f"korea_orderbook",
            f"korea_ticker",
            f"asia_orderbook",
            f"asia_ticker",
            f"ne_orderbook",
            f"ne_ticker",
        ]

        # 파티션 설정 (거래소 기반 파티셔닝에 최적화)
        # - 한국: 업비트, 빗썸, 코인원, 코빗 + 여유 파티션 고려
        # - 아시아: 바이낸스, 후오비, OKX, 비트겟 등 고려
        # - 북미/유럽: 코인베이스, 바이낸스US, 크라켄, FTX 등 고려
        partition = [6, 6, 4, 4, 4, 4]

        print("Creating topics with the following configuration:")
        for i, (t, p) in enumerate(zip(topic, partition)):
            print(f"  {i+1}. {t}: {p} partitions")

        # 복제 계수는 높은 가용성을 위해 3으로 유지
        replication = [3] * len(topic)

        return new_topic_initialization(
            topic=topic,
            partition=partition,
            replication_factor=replication,
        )
    except Exception as error:
        print(f"Error creating topics: {error}")


def clear_all_topics() -> None:
    """
    모든 토픽을 삭제합니다.
    주의: 개발 환경에서만 사용하세요!
    """
    try:
        delete_all_topics()
        print("All topics deleted successfully.")
    except Exception as error:
        print(f"Error deleting topics: {error}")


if __name__ == "__main__":
    data_sending_start()
