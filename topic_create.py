from mq.data_admin import new_topic_initialization, delete_all_topics
from common.setting.properties import (
    KOREA_REAL_TOPIC_NAME,
    ASIA_REAL_TOPIC_NAME,
    NE_REAL_TOPIC_NAME,
)


def data_sending_start() -> None:
    """
    Topic create
    """
    try:
        topic = [
            f"{ASIA_REAL_TOPIC_NAME}BTC",
            f"{KOREA_REAL_TOPIC_NAME}BTC",
            f"{NE_REAL_TOPIC_NAME}BTC",
            "Region.NE_OrderbookPreprocessing",
            "Region.Asia_OrderbookPreprocessing",
            "Region.Korea_OrderbookPreprocessing",
            "Region.Korea_TickerPreprocessing",
            "Region.Asia_TickerPreprocessing",
            "Region.NE_TickerPreprocessing",
        ]
        partition = [2] * len(topic)
        replication = [3] * len(topic)

        return new_topic_initialization(
            topic=topic, partition=partition, replication_factor=replication
        )
    except Exception as error:
        print(error)


if __name__ == "__main__":
    data_sending_start()
