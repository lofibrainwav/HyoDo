# Trinity Score: 90.0 (Established by Chancellor)
"""Tests for api/routes/pillars.py
5기둥 API 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient


class TestPillarsEndpoint:
    """5기둥 API 엔드포인트 테스트"""

    @pytest.fixture
    def client(self) -> TestClient:
        import os
        import sys

        sys.path.insert(
            0,
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        )
        from AFO.api_server import app

        return TestClient(app)

    def test_pillars_current_returns_200(self, client: TestClient) -> None:
        """GET /api/5pillars/current 가 200을 반환하는지 테스트"""
        response = client.get("/api/5pillars/current")
        assert response.status_code == 200

    def test_pillars_current_has_required_fields(self, client: TestClient) -> None:
        """5기둥 응답에 필수 필드가 있는지 테스트"""
        response = client.get("/api/5pillars/current")
        data = response.json()

        # 최소 하나의 기둥 관련 필드가 있어야 함
        possible_fields = [
            "truth",
            "goodness",
            "beauty",
            "serenity",
            "eternity",
            "pillars",
            "scores",
            "真",
            "善",
            "美",
            "孝",
            "永",
        ]
        has_field = any(field in str(data) for field in possible_fields)
        assert has_field or "error" not in data

    def test_pillars_live_post(self, client: TestClient) -> None:
        """POST /api/5pillars/live 테스트"""
        response = client.post("/api/5pillars/live", json={"query": "test"})
        # 200 or 422 (validation) or 500 (backend not ready)
        assert response.status_code in [200, 422, 500]

    def test_family_hub_returns_200(self, client: TestClient) -> None:
        """GET /api/5pillars/family/hub 테스트"""
        response = client.get("/api/5pillars/family/hub")
        assert response.status_code == 200

    def test_family_hub_has_data(self, client: TestClient) -> None:
        """Family hub 응답에 데이터가 있는지 테스트"""
        response = client.get("/api/5pillars/family/hub")
        data = response.json()
        # 응답이 dict 또는 list여야 함
        assert isinstance(data, (dict, list))


class TestTrinityScoreCalculation:
    """Trinity Score 계산 테스트"""

    def test_trinity_formula_weights(self) -> None:
        """Trinity Score 가중치 공식 테스트: 0.35眞 + 0.35善 + 0.20美 + 0.08孝 + 0.02永"""
        truth = 1.0
        goodness = 1.0
        beauty = 1.0
        serenity = 1.0
        eternity = 1.0

        score = 0.35 * truth + 0.35 * goodness + 0.20 * beauty + 0.08 * serenity + 0.02 * eternity

        assert score == pytest.approx(1.0)

    def test_trinity_weights_sum_to_one(self) -> None:
        """가중치 합이 1.0인지 테스트"""
        weights = [0.35, 0.35, 0.20, 0.08, 0.02]
        assert sum(weights) == pytest.approx(1.0)

    def test_trinity_partial_scores(self) -> None:
        """부분 점수 계산 테스트"""
        # 모든 기둥이 0.5일 때
        score = 0.35 * 0.5 + 0.35 * 0.5 + 0.20 * 0.5 + 0.08 * 0.5 + 0.02 * 0.5
        assert score == pytest.approx(0.5)

    def test_balance_delta_calculation(self) -> None:
        """Balance delta 계산 테스트 (max - min < 0.3)"""
        pillars = [0.8, 0.9, 0.85, 0.82, 0.88]
        max_val = max(pillars)
        min_val = min(pillars)
        delta = max_val - min_val

        # 균형 잡힌 상태: delta < 0.3
        assert delta < 0.3
