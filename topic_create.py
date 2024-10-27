from mq.data_admin import new_topic_initialization
from common.setting.properties import (
    KOREA_REAL_TOPIC_NAME,
    ASIA_REAL_TOPIC_NAME,
    NE_REAL_TOPIC_NAME,
)


def data_sending_start() -> None:
    """
    Topic creation based on regional partition requirements:
    - Korea: 4 partitions
    - Asia: 3 partitions
    - NE: 2 partitions
    """
    try:
        topic = [
            f"{KOREA_REAL_TOPIC_NAME}BTC-orderbook",
            f"{KOREA_REAL_TOPIC_NAME}BTC-ticker",
            f"{ASIA_REAL_TOPIC_NAME}BTC-orderbook",
            f"{ASIA_REAL_TOPIC_NAME}BTC-ticker",
            f"{NE_REAL_TOPIC_NAME}BTC-orderbook",
            f"{NE_REAL_TOPIC_NAME}BTC-ticker",
            "Region.NE_OrderbookPreprocessing",
            "Region.Asia_OrderbookPreprocessing",
            "Region.Korea_OrderbookPreprocessing",
            "Region.Korea_TickerPreprocessing",
            "Region.Asia_TickerPreprocessing",
            "Region.NE_TickerPreprocessing",
        ]

        # Partition settings by region (matching the topic order above)
        partition = [4, 4, 3, 3, 2, 2, 2, 3, 4, 4, 3, 2]
        replication = [3] * len(topic)

        return new_topic_initialization(
            topic=topic, partition=partition, replication_factor=replication
        )
    except Exception as error:
        print(f"Error creating topics: {error}")


if __name__ == "__main__":
    data_sending_start()
