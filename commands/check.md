---
description: "AFO 4-Gate CI 프로토콜 실행 (眞善美永)"
allowed-tools: Bash(hyodo:*), Bash(ruff:*), Bash(pyright:*), Bash(pytest:*), Read
impact: CRITICAL
tags: [ci, quality, testing, lint]
---

# AFO 4-Gate CI Lock Protocol

CI Lock Protocol을 실행하여 코드 품질을 검증합니다.

## 4-Gate 순서

1. **眞 (Truth) - Pyright**: 타입 체크
2. **美 (Beauty) - Ruff**: 린트 + 포맷
3. **善 (Goodness) - pytest**: 유닛 테스트
4. **永 (Eternity) - SBOM**: 보안 봉인 (리포 checkout + 스크립트 있을 때만)

## 실행 (권장)

벤더 무관 CLI:

```bash
# 패키지 설치 후
pip install -e ".[dev]"
hyodo check
```

공개 패키지 게이트를 CI와 동일하게 수동 실행:

```bash
ruff check hyodo/ --output-format=concise
ruff format --check hyodo/
pyright hyodo
pytest -q --tb=short
```

> Makefile-based check targets are not provided in this repository. CI SSOT is `.github/workflows/ci.yml` and `hyodo check`.

## 개별 게이트 실행

- `pyright hyodo` — 타입 체크 (공개 패키지)
- `ruff check hyodo/` — 린트
- `ruff format --check hyodo/` — 포맷
- `pytest -q` — 테스트

## 결과 해석

- **PASS**: 모든 게이트 통과 → 커밋/PR 후보 (사람 리뷰는 별도)
- **FAIL**: 실패 게이트 수정 후 재실행

게이트 통과는 자동 merge/자동 배포 승인이 아닙니다.

## Evidence 기록

```text
Gate: [Pyright|Ruff|pytest|SBOM]
Status: [PASS|FAIL]
Details: [에러 요약 또는 OK]
```
