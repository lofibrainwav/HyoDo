"""Port Data Provider

포트 데이터 제공자.
"""


class PortDataProvider:
    """
    포트 데이터 제공자

    Trinity Score: 美 (Beauty) - 체계적이고 읽기 쉬운 데이터 구조
    """

    @staticmethod
    def get_port_data() -> dict[str, str]:
        """서비스 포트 매핑 데이터 반환"""
        return [
            {"service": "Soul Engine", "port": "8010", "description": "FastAPI 백엔드"},
            {
                "service": "Dashboard",
                "port": "3000",
                "description": "Next.js 프론트엔드",
            },
            {"service": "Ollama", "port": "11434", "description": "LLM (영덕)"},
            {"service": "Redis", "port": "6379", "description": "캐시/세션"},
            {"service": "PostgreSQL", "port": "15432", "description": "데이터베이스"},
            {"service": "Grafana", "port": "3100", "description": "모니터링"},
            {"service": "Prometheus", "port": "9090", "description": "메트릭"},
        ]
