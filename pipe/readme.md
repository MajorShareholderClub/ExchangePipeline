## pipe folder 의 역할 

📂 pipe

📡 데이터 전송 및 처리 관련 모듈을 포함한 디렉토리
이 디렉토리는 다양한 거래소와의 통신을 위한 클라이언트를 포함하여, 소켓과 REST API를 통한 데이터 전송 및 처리를 담당합니다.


### commmon file 구조 
```
📂 pipe                                  # 📡 데이터 전송 및 처리 관련 모듈을 포함한 디렉토리
├── 📂 common                            # 🛠️ 공통으로 사용되는 소켓 관련 모듈
│   └── 🐍 socket_common.py              # 소켓 통신을 위한 공통 기능 및 유틸리티 함수
├── 📂 foreign                           # 🌍 해외 거래소와의 통신을 위한 클라이언트
│   ├── 🐍 foreign_rest_client.py        # 해외 거래소의 REST API 클라이언트 │구현
│   └── 🐍 foreign_websocket_client.py   # 해외 거래소의 웹소켓 클라이언트 구현
├── 📂 korea                             # 🇰🇷 한국 거래소와의 통신을 위한 클라이언트
│   ├── 🐍 korea_rest_client.py          # 한국 거래소의 REST API 클라이언트 구현
│   └── 🐍 korea_websocket_client.py     # 한국 거래소의 웹소켓 클라이언트 구현
```
