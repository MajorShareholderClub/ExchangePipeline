## config folder 의 역할 

📂 config

🗂️ 설정 관련 파일을 모아둔 디렉토리
이 디렉토리는 시스템의 다양한 설정 파일을 포함하여 API 및 소켓 연결에 필요한 설정값을 관리합니다.

주요 서브디렉토리 및 파일


### commmon file 구조 
```
📂 config                      # 🗂️ 설정 관련 파일을 모아둔 디렉토리
├── 🐍 json_param_load.py      # json 로드 하여 class 주소값과 함께 보내주는 파일
├── 📂 foreign                 # 해외 거래소 설정
│   ├── 🔧 _market_rest.json   # 해외 거래소 REST API 설정
│   └── 🔧 _market_socket.json # 해외 거래소 소켓 설정
├── 📂 korea                   # 한국 거래소 설정
│   ├── 🔧 _market_rest.json   # 한국 거래소 REST API 설정
│   └── 🔧 _market_socket.json # 한국 거래소 소켓 설정
└── 📂 types                   # 설정 관련 데이터 타입 정의
    ├── 🐍 __init__.py         # 타입 모듈 초기화 파일
    └── 🐍 _exchange.py        # 거래소 타입 정의
```
