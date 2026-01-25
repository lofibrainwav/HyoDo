# PH23 V1 잔재 체크리스트 (SSOT)

## 상태: ✅ 정복 완료

---

## V1 잔재 분류

### ✅ 허용됨 (Deprecated Fallback)

| 파일 | 이유 |
|------|------|
| `chancellor_router.py` | V2 우선, V1 폴백 |
| `initialization.py` | V2 우선, V1 폴백 |
| `integrity_check.py` | V2 우선, V1 폴백 |
| `AFO/__init__.py` | lazy import V2 우선 |

> V1 fallback은 롤백 안전장치로 유지

---

### ✅ 아카이브됨

```
legacy/archived/
├── chancellor_graph.py
├── AFO/chancellor_graph.py
├── mediators/chancellor_mediator.py
└── verify_chancellor_graph.py
```

---

### ✅ CI Gate 활성

```bash
scripts/ci_v1_import_ban.sh
# V1 파일이 active codebase에 없는지 확인
```

---

## 정복 확인 명령

```bash
# CI Gate
bash scripts/ci_v1_import_ban.sh

# Contract Test
python scripts/chancellor_v2_contract_test.py

# Integration Test
python scripts/chancellor_v2_integration_test.py
```

---

## PH24 제안

1. `legacy/archived/` PYTHONPATH 제외 확인
2. V1 문서 업데이트/삭제
3. 라우팅 레벨 V1 접근 차단
