## common folder 의 역할 

📂 common

🛠️ 공통으로 사용되는 모듈을 모아놓은 디렉토리
이 디렉토리는 다양한 모듈들이 서로 상호작용할 수 있도록 공통 기능과 인터페이스를 제공하여, 코드의 재사용성과 유지 보수성을 높이는 역할을 합니다.



### 📂 common                   # 🛠️ 공통으로 사용되는 모듈을 모아놓은 디렉토리
```
├── 📂 client                   # 🌐 API 클라이언트와 거래소 인터페이스 관련 모듈
│   ├── 📂 market_rest          # REST API 클라이언트 관련 모듈
│   │   ├── 🐍 async_api_client.py        # 비동기 API 호출을 위한 클라이언트 구현
│   │   └── 🐍 rest_interface.py          # 거래소 REST 호출 인터페이스 정의
│   └── 📂 market_socket        # 소켓 클라이언트 관련 모듈
│       ├── 🐍 async_socket_client.py     # 비동기 소켓 클라이언트 구현
│       └── 🐍 websocket_interface.py     # 거래소 웹소켓 호출 인터페이스 정의
├── 📂 core                     # ⚙️ 핵심 로직 및 추상화된 구조를 포함한 디렉토리
│   ├── 📂 abstract             # 📝 추상화된 클래스들을 모아둔 하위 디렉토리
│   │   ├── 🐍 __init__.py      # 추상 모듈 초기화 파일
│   │   ├── 🐍 abstract_async_request.py  # 비동기 요청을 추상화한 클래스
│   │   ├── 🐍 abstract_stream.py        # 스트림 처리 추상 클래스
│   │   └── 🐍 abstract_trade_api.py     # 거래 API 추상 클래스
│   ├── 🐍 data_format.py       # 데이터 포맷 변환 및 처리 모듈
│   └── 📂 types               # 🗂️ 공통 데이터 타입 정의 모듈
│       ├── 🐍 __init__.py      # 타입 모듈 초기화 파일
│       └── 🐍 _common_exchange.py # 거래소 관련 공통 데이터 타입 정의
├── 📂 exception                # ❗ 예외 처리를 위한 모듈
│   ├── 🐍 __init__.py          # 예외 처리 모듈 초기화 파일
│   └── 🐍 exception.py         # 커스텀 예외 정의
├── 📜 readme.md               # common 디렉토리에 대한 설명을 담고 있는 파일
├── 📂 setting                  # ⚙️ 설정 파일 관련 모듈
│   ├── 🐍 properties.py         # 기본 속성 및 설정 값 관리
│   ├── 🐍 socket_parameter.py    # 소켓 연결 파라미터 정의
│   └── 🐍 urls.conf            # API 엔드포인트 URL 설정
└── 📂 utils                   # 🧰 공통 유틸리티 함수 모음
    ├── 🐍 logger.py           # 로그 관리 모듈
    └── 🐍 other_util.py       # 기타 유틸리티 함수들
```
