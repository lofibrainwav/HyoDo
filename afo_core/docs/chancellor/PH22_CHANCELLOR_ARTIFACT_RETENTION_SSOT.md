# PH22 — Chancellor Artifacts Retention SSOT (1-page)

## Goal

chancellor_v2 trace/events/checkpoints 아티팩트가 누적되어 운영 피로(디스크/속도)를 유발하지 않도록
**"보존 정책 + 정리 스크립트 + 적용 규칙"**을 SSOT로 봉인한다.

---

## Scope

| 유형 | 경로 |
|------|------|
| Events | `artifacts/chancellor_events/*.jsonl` |
| Checkpoints | `artifacts/chancellor_checkpoints/{trace_id}/*.json` |

---

## Retention Policy

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `--keep-traces` | 200 | 최근 N개 trace 유지 |
| `--keep-days` | 14 | 최근 D일 유지 |

### 삭제 조건
- **둘 다 만족해야 삭제**: 최근 200개에 포함되지 않고 **AND** 14일 이상 지난 trace

### 안전장치
- **기본 DRY-RUN**: 삭제 대상만 출력, 실제 삭제 없음
- **--apply**: 실제 삭제 실행

---

## 정리 대상

1. 오래된 trace의 events 파일 (`.jsonl`)
2. 해당 trace의 checkpoints 디렉토리
3. orphan checkpoints (events 없는 trace_id도 동일 기준)

---

## Success Criteria

- [ ] DRY-RUN에서 삭제 대상/용량/개수 요약이 결정론적으로 출력
- [ ] `--apply` 실행 시 실제 파일 삭제
- [ ] 재실행하면 삭제 대상 0

---

## Usage

```bash
# DRY-RUN (기본)
python scripts/prune_chancellor_artifacts.py --keep-traces 200 --keep-days 14

# 실제 삭제
python scripts/prune_chancellor_artifacts.py --keep-traces 200 --keep-days 14 --apply
```

---

## Rollback

- `--apply` 이전에는 변경 없음
- `--apply` 이후 복구는 git 대상이 아니므로, 필요시 백업에서 복원

---

## CI Integration (선택)

```yaml
# .github/workflows/prune-artifacts.yml
- name: Prune old artifacts
  run: python scripts/prune_chancellor_artifacts.py --keep-traces 200 --keep-days 14 --apply
  schedule:
    - cron: '0 3 * * *'  # 매일 03:00 UTC
```
