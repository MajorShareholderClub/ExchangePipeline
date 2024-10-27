### 클라이언트 모듈 설명

각 거래소의 REST API 와 WebSocket 요청을 처리하기 위한 클라이언트 클래스들이 포함되어 있습니다.

### 📂 protocols               # 🌐 거래소와의 통신을 위한 클라이언트 모듈
```
├── 📂 client                  # 💻 각 지역별 거래소 클라이언트 모듈
│   ├── 📂 asia                # 🌏 아시아 거래소 클라이언트
│   │   ├── 🐍 rest_asia_exchange.py     # 아시아 거래소 REST API 처리 모듈
│   │   └── 🐍 socket_asia_exchange.py   # 아시아 거래소 소켓 API 처리 모듈
│   ├── 📂 korea               # 🇰🇷 한국 거래소 클라이언트
│   │   ├── 🐍 rest_korea_exchange.py    # 한국 거래소 REST API 처리 모듈
│   │   └── 🐍 socket_korea_exchange.py  # 한국 거래소 소켓 API 처리 모듈
│   └── 📂 ne                  # 🌍 해외 거래소 클라이언트
│       ├── 🐍 rest_ne_exchange.py        # 해외 거래소 REST API 처리 모듈
│       └── 🐍 socket_ne_exchange.py      # 해외 거래소 소켓 API 처리 모듈
├── 📂 connection              # 🔗 API 연결 관련 모듈
│   ├── 🐍 coin_rest_api.py    # 코인 REST API 연결 모듈
│   └── 🐍 coin_socket.py       # 코인 소켓 연결 모듈
└── 📜 readme.md              # protocols 디렉토리에 대한 설명을 담고 있는 파일
```

### REST API 프로세스 구조 
```mermaid
classDiagram
    class AbstractExchangeRestClient {
        +get_coin_all_info_price(coin_name: str): ExchangeResponseData
    }
    class CoinExchangeRestClient {
        +get_coin_all_info_price(coin_name: str): ExchangeResponseData
    }
    class ClassNE {
        +BinanceRest
        +KrakenRest
    }
    class ClassKorea {
        +UpbitRest
        +BithumbRest
        +CoinoneRest
        +KorbitRest
    }
    class ClassAsia {
        +GateIORest
        +BybitRest
        +OKXRest
    }

    AbstractExchangeRestClient <|-- CoinExchangeRestClient
    CoinExchangeRestClient <|-- ClassNE
    CoinExchangeRestClient <|-- ClassKorea
    CoinExchangeRestClient <|-- ClassAsia
```

### WebSocket 프로세스 구조
```mermaid      
classDiagram
    class AbstractExchangeSocketClient {
        +get_present_websocket(symbol: str, req_type: str, socket_type: str): Coroutine
    }
    class CoinExchangeSocketClient {
        +get_present_websocket(symbol: str, req_type: str, socket_type: str): None
    }
    class NEWebsocketConnection {
        +websocket_to_json(uri: str, subs_fmt: list[dict], symbol: str, socket_type: str): None
    }
    class KoreaWebsocketConnection {
        +websocket_to_json(uri: str, subs_fmt: list[dict], symbol: str, socket_type: str): None
    }
    class AsiaWebsocketConnection {
        +websocket_to_json(uri: str, subs_fmt: list[dict], symbol: str, socket_type: str): None
    }
    class ClassNE {
        +BinanceSocket
        +KrakenSocket
    }
    class ClassKorea {
        +UpbitSocket
        +BithumbSocket
        +CoinoneSocket
        +KorbitSocket
    }
    class ClassAsia {
        +GateIOSocket
        +BybitSocket
        +OKXSocket
    }

    AbstractExchangeSocketClient <|-- CoinExchangeSocketClient
    CoinExchangeSocketClient <|-- ClassNE
    CoinExchangeSocketClient <|-- ClassKorea
    CoinExchangeSocketClient <|-- ClassAsia
    ClassNE --> NEWebsocketConnection : uses
    ClassKorea --> KoreaWebsocketConnection : uses
    ClassAsia --> AsiaWebsocketConnection : uses
```

--------------------------------

### Websocket Connection Manager 프로세스 구조
```mermaid
classDiagram
    class WebsocketConnectionManager {
        +websocket_to_json(uri: str, subs_fmt: list[dict], symbol: str): None
    }
    class BaseMessageDataPreprocessing {
        +put_message_to_logging(market: str, symbol: str, message: ResponseData): None
        +send_kafka_message(market: str, symbol: str, data: list, topic: str, key: str): None
    }
    class MessageDataPreprocessing {
        +put_message_to_logging(message: ResponseData, uri: str, symbol: str): None
    }
    class AsiaWebsocketConnection {
        +websocket_to_json(uri: str, subs_fmt: list[dict], symbol: str): None
    }
    class NEWebsocketConnection {
        +websocket_to_json(uri: str, subs_fmt: list[dict], symbol: str): None
    }
    class KoreaWebsocketConnection {
        +websocket_to_json(uri: str, subs_fmt: list[dict], symbol: str): None
    }

    WebsocketConnectionManager <|-- AsiaWebsocketConnection
    WebsocketConnectionManager <|-- NEWebsocketConnection
    WebsocketConnectionManager <|-- KoreaWebsocketConnection
    BaseMessageDataPreprocessing <|-- MessageDataPreprocessing
    MessageDataPreprocessing --> BaseMessageDataPreprocessing : extends
    AsiaWebsocketConnection --> MessageDataPreprocessing : uses
    NEWebsocketConnection --> MessageDataPreprocessing : uses
    KoreaWebsocketConnection --> MessageDataPreprocessing : uses
```

### REST Connection Manager 프로세스 구조
```mermaid
classDiagram
    class BaseExchangeRestAPI {
        +total_pull_request(coin_symbol: str, interval: int): None
    }
    class ExchangeRestAPI {
        +create_schema(market_result: list[ExchangeData]): dict
    }
    class KoreaExchangeRestAPI {
        +__init__()
    }
    class NEExchangeRestAPI {
        +__init__()
    }
    class AsiaExchangeRestAPI {
        +__init__()
    }
    class KafkaMessageSender {
        +produce_sending(message: dict, topic: str, key: str): None
    }
    class CoinHashingCustomPartitional

    BaseExchangeRestAPI <|-- ExchangeRestAPI
    ExchangeRestAPI <|-- KoreaExchangeRestAPI
    ExchangeRestAPI <|-- NEExchangeRestAPI
    ExchangeRestAPI <|-- AsiaExchangeRestAPI
    ExchangeRestAPI --> KafkaMessageSender : uses
    KafkaMessageSender --> CoinHashingCustomPartitional : uses
``` 

