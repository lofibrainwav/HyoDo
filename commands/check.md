---
description: "AFO 4-Gate CI 프로토콜 실행 (眞善美永)"
allowed-tools: Bash(make:*), Read
impact: CRITICAL
tags: [ci, quality, testing, lint]
---

# AFO 4-Gate CI Lock Protocol

CI Lock Protocol을 실행하여 코드 품질을 검증합니다.

## 4-Gate 순서

1. **眞 (Truth) - Pyright**: 타입 체크
2. **美 (Beauty) - Ruff**: 린트 + 포맷
3. **善 (Goodness) - pytest**: 유닛 테스트
4. **永 (Eternity) - SBOM**: 보안 봉인

## 실행

```bash
make check
```

> 워크스페이스 루트에서 실행됩니다.

## 개별 게이트 실행

- `make type-check` - Pyright만
- `make lint` - Ruff만
- `make test` - pytest만

## 결과 해석

- **PASS**: 모든 게이트 통과 → 커밋 가능
- **FAIL**: 실패 게이트 수정 후 재실행

## Evidence 기록

실행 결과를 아래 형식으로 기록:
```
Gate: [Pyright|Ruff|pytest|SBOM]
Status: [PASS|FAIL]
Details: [에러 요약 또는 OK]
```
