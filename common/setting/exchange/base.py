from pathlib import Path
from abc import abstractmethod
import yaml


class BaseSocketParameter:
    """거래소 파라미터 생성기의 기본 클래스

    공통 기능을 제공하는 추상 기본 클래스
    """

    def __init__(self, exchange: str, region: str) -> None:
        self.exchange = exchange
        self.region = region
        self.template_path = self._get_template_path()
        self.template = self._load_template()

    def _get_template_path(self) -> Path:
        """템플릿 파일 경로 생성"""
        base_dir = Path(__file__).parent.parent
        return (
            base_dir
            / "config"
            / "socket_templates"
            / self.region
            / f"{self.exchange}.yml"
        )

    def _load_template(self) -> dict:
        """YAML 템플릿 로드"""
        if not self.template_path.exists():
            raise FileNotFoundError(
                f"템플릿 파일을 찾을 수 없습니다: {self.template_path}"
            )

        with open(self.template_path, "r") as f:
            return yaml.safe_load(f)

    @abstractmethod
    def create_parameters(self, symbols: list[str], req_type: str) -> dict | list[dict]:
        """파라미터 생성 (서브클래스에서 구현)"""
        raise NotImplementedError("서브클래스에서 구현해야 합니다")
