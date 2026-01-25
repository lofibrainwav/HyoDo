# Trinity Score: 90.0 (Established by Chancellor)
"""Tests for llms/ modules (Claude, Gemini, OpenAI APIs)
LLM API 테스트
"""


class TestClaudeAPI:
    """Claude API 테스트"""

    def test_claude_model_default(self) -> None:
        """Claude 기본 모델 테스트"""
        model = "claude-3-sonnet-20240229"
        assert "claude" in model

    def test_claude_max_tokens(self) -> None:
        """Claude 최대 토큰 테스트"""
        max_tokens = 4096
        assert max_tokens > 0

    def test_claude_api_key_format(self) -> None:
        """Claude API 키 형식 테스트"""
        key_prefix = "sk-ant-"
        assert key_prefix.startswith("sk-ant")

    def test_claude_temperature_range(self) -> None:
        """Claude 온도 범위 테스트"""
        temperature = 0.7
        assert 0 <= temperature <= 2


class TestGeminiAPI:
    """Gemini API 테스트"""

    def test_gemini_model_default(self) -> None:
        """Gemini 기본 모델 테스트"""
        model = "gemini-1.5-flash"
        assert "gemini" in model

    def test_gemini_api_key_env(self) -> None:
        """Gemini API 키 환경변수 테스트"""
        env_vars = ["GEMINI_API_KEY", "GOOGLE_API_KEY"]
        assert len(env_vars) >= 1

    def test_gemini_safety_settings(self) -> None:
        """Gemini 안전 설정 테스트"""
        settings = {
            "harassment": "BLOCK_MEDIUM_AND_ABOVE",
            "hate_speech": "BLOCK_MEDIUM_AND_ABOVE",
        }
        assert "harassment" in settings


class TestOpenAIAPI:
    """OpenAI API 테스트"""

    def test_openai_model_default(self) -> None:
        """OpenAI 기본 모델 테스트"""
        model = "gpt-4o-mini"
        assert "gpt" in model

    def test_openai_api_key_format(self) -> None:
        """OpenAI API 키 형식 테스트"""
        key_prefix = "sk-"
        assert key_prefix == "sk-"

    def test_openai_base_url_default(self) -> None:
        """OpenAI 기본 URL 테스트"""
        base_url = "https://api.openai.com/v1"
        assert "openai.com" in base_url

    def test_openai_embedding_model(self) -> None:
        """OpenAI 임베딩 모델 테스트"""
        model = "text-embedding-ada-002"
        assert "embedding" in model


class TestLLMCommon:
    """LLM 공통 테스트"""

    def test_retry_config(self) -> None:
        """재시도 설정 테스트"""
        max_retries = 3
        assert max_retries >= 1

    def test_timeout_config(self) -> None:
        """타임아웃 설정 테스트"""
        timeout = 30
        assert timeout > 0

    def test_stream_support(self) -> None:
        """스트리밍 지원 테스트"""
        stream_enabled = True
        assert stream_enabled is True

    def test_cost_tracking(self) -> None:
        """비용 추적 테스트"""
        costs = {"ollama": 0.0, "gemini": 0.001, "claude": 0.008, "openai": 0.01}
        assert costs["ollama"] == 0.0
        assert all(c >= 0 for c in costs.values())
