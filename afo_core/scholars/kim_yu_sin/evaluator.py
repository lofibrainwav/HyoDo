class QualityEvaluator:
    """Yeongdeok 품질 평가 로직"""

    @staticmethod
    def evaluate_code_quality(response: str, query: str) -> float:
        """
        코드 응답 품질 평가
        Trinity Score (0-100) 추정
        """
        score = 85.0  # 코드는 기본 점수 높게

        # 眞: 코드 블록 확인
        if "```" in response:
            score += 5.0
            # Python 코드 블록이면 추가 점수
            if "```python" in response.lower() or "def " in response or "class " in response:
                score += 5.0

        # 善: 오류 패턴 검사
        error_patterns = ["SyntaxError", "IndentationError", "오류", "실패", "Error:"]
        if any(p in response for p in error_patterns):
            score -= 25.0

        # 美: 주석/독스트링 포함
        if '"""' in response or "'''" in response or "# " in response:
            score += 3.0

        # 응답 길이 (코드는 적당히 길어야)
        if len(response) < 100:
            score -= 10.0

        # 쿼리 키워드 관련성 확인
        query_keywords = {"함수", "클래스", "구현", "작성", "만들", "def", "class", "function"}
        query_has_code_keywords = any(kw in query.lower() for kw in query_keywords)
        response_has_code = "def " in response or "class " in response
        if query_has_code_keywords and response_has_code:
            score += 3.0

        return max(0.0, min(100.0, score))

    @staticmethod
    def evaluate_response_quality(response: str, query: str) -> float:
        """
        응답 품질 간이 평가 (Trinity Score 추정)
        """
        score = 80.0  # 기본 점수

        # 眞: 응답 길이 (너무 짧으면 감점)
        if len(response) < 50:
            score -= 15.0
        elif len(response) > 200:
            score += 5.0

        # 善: 오류 패턴 검사
        error_patterns = ["오류", "실패", "error", "failed", "처리 실패", "Error:"]
        if any(p.lower() in response.lower() for p in error_patterns):
            score -= 20.0

        # 美: 구조화 (리스트, 코드블록 등)
        if "- " in response or "1." in response or "```" in response:
            score += 5.0

        # 쿼리 키워드 포함 여부 (관련성)
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words & response_words)
        if overlap >= 2:
            score += 5.0

        return max(0.0, min(100.0, score))
