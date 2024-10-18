## config folder 의 역할 

📂 config

🗂️ 설정 관련 파일을 모아둔 디렉토리
이 디렉토리는 시스템의 다양한 설정 파일을 포함하여 API 및 소켓 연결에 필요한 설정값을 관리합니다.

주요 서브디렉토리 및 파일

### 📂 config                   # 🗂️ 설정 관련 파일을 모아둔 디렉토리
```
├── 📂 asia                     # 🌏 아시아 거래소 관련 설정
│   ├── 🔧 _market_rest.yml     # 아시아 거래소 REST API 설정
│   └── 🔧 _market_socket.yml    # 아시아 거래소 소켓 설정
├── 📂 korea                    # 🇰🇷 한국 거래소 관련 설정
│   ├── 🔧 _market_rest.yml     # 한국 거래소 REST API 설정
│   └── 🔧 _market_socket.yml    # 한국 거래소 소켓 설정
├── 📂 ne                       # 🏦 북미 거래소 관련 설정
│   ├── 🔧 _market_rest.yml     # 북미 거래소 REST API 설정
│   └── 🔧 _market_socket.yml    # 북미 거래소 소켓 설정
├── 📜 readme.md               # config 디렉토리에 대한 설명을 담고 있는 파일
├── 📂 types                   # 📂 설정 관련 데이터 타입 정의
│   ├── 🐍 __init__.py          # 타입 모듈 초기화 파일
│   └── 🐍 _exchange.py         # 거래소 타입 정의
└── 🐍 yml_param_load.py       # yml 파라미터 로드 모듈
```
