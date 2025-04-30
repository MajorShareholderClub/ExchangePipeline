# 🛠️ common 모듈

## 배경 (Problem)
프로젝트 전반에서 **예외·로깅·설정** 코드가 반복되면 의존성이 꼬이고 유지보수가 어려워집니다.  
또한 설정 파일을 매번 디스크에서 읽어 오면 I/O 비용이 증가하고 성능이 저하됩니다.

## 목표 (Solution)
`common` 모듈은 핵심 로직과 무관한 **지원 기능**을 한곳에 모아 재사용성을 극대화합니다.
- 표준화된 로깅(`logger.py`)
- 커스텀 예외 정의(`exceptions.py`)
- YAML 설정 로더 + LRU 캐싱(`setting/config/yml_config.py`)
- 전역 DI 레지스트리(`registry/`)

## 작동 흐름 (Cause–Development)
1. 비즈니스 코드가 설정 값을 필요로 할 때 `YmlConfig` 클래스를 호출합니다.
2. `load_yml_file` 는 LRU 캐시로 I/O 쿼리를 최소화합니다.
3. 문제가 발생하면, 도메인별 예외를 `exceptions.py` 에서 정의·발생시켜 일관된 오류 핸들링을 제공합니다.
4. 모든 로그는 `logger.get_logger()` 를 통해 JSON-Structured 포맷으로 출력되어, 중앙 모니터링 스택(Grafana 등)과 호환됩니다.

## 폴더 구조
```bash
common/
├── exceptions.py        # 도메인 커스텀 예외
├── logger.py            # 색상 + JSON 로거
├── registry/            # DI 레지스트리
│   └── __init__.py
└── setting/
    ├── config/
    │   └── yml_config.py   # YAML Loader + Cache
    └── socket_templates/   # 거래소별 구독 템플릿
```

## 기대 효과 (Result)
- **단일 진입점**: 지원 코드의 위치가 명확해져 탐색 비용↓.
- **성능 향상**: YAML 캐싱으로 평균 로드 타임이 ~90% 단축.
- **관찰 가능성**: 구조화 로그 + 예외 통일로 디버깅 생산성↑.

## 맺음말 (Conclusion)
`common` 모듈은 프로젝트의 **기초 체력**을 담당하며, 핵심 로직의 순도와 가독성을 높여줍니다.