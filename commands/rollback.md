---
description: "장애 시 자동 롤백 워크플로우"
allowed-tools: Bash(git:*), Bash(docker:*), Read, Grep
impact: CRITICAL
tags: [rollback, recovery, disaster, goodness, stability]
---

# Rollback - 자동 복구 워크플로우

$ARGUMENTS 상황에 대한 롤백을 수행합니다.

## 롤백 트리거 조건

| 트리거          | 자동 롤백 | 수동 확인 |
| ------------ | ----- | ----- |
| CI 4-Gate 실패 | ❌     | ✅ ASK |
| Health 체크 실패 | ❌     | ✅ ASK |
| 프로덕션 에러 급증   | ❌     | ✅ ASK |
| 사용자 명시 요청    | -     | ✅ 즉시  |

## Phase 1: 롤백 지점 분석

### 최근 안정 커밋 찾기
```bash
# CI 통과한 최근 커밋
git log --oneline -20 | head -10

# 특정 파일의 마지막 안정 버전
git log --oneline -5 -- [파일경로]

# 태그된 릴리스
git tag -l --sort=-creatordate | head -5
```

### 롤백 영향 분석
```bash
# 롤백 시 되돌려지는 변경
git diff [target_commit]..HEAD --stat

# 영향받는 파일 수
git diff [target_commit]..HEAD --name-only | wc -l
```

## Phase 2: 롤백 전략 선택

### Strategy A: Soft Rollback (Revert)
```bash
# 특정 커밋 되돌리기 (새 커밋 생성)
git revert [commit_hash] --no-edit

# 여러 커밋 되돌리기
git revert [older_commit]..[newer_commit] --no-edit
```

**장점**: 히스토리 보존, 안전
**단점**: 복잡한 충돌 가능

### Strategy B: Hard Rollback (Reset)
```bash
# 특정 커밋으로 강제 이동 (히스토리 삭제)
git reset --hard [commit_hash]

# 원격에도 반영 (주의!)
git push --force-with-lease
```

**장점**: 깔끔한 히스토리
**단점**: 작업 손실 위험, 협업 시 문제

### Strategy C: Branch Rollback
```bash
# 롤백 브랜치 생성
git checkout -b rollback/[issue] [safe_commit]

# 메인에 머지
git checkout main && git merge rollback/[issue]
```

**장점**: 안전, 검토 가능
**단점**: 추가 단계 필요

## Phase 3: 롤백 실행

### Pre-Rollback 체크리스트

- [ ] 롤백 대상 커밋 확인
- [ ] 영향받는 파일 목록 확인
- [ ] 다른 에이전트 작업 충돌 확인 (/council)
- [ ] 데이터 손실 가능성 확인

### 롤백 실행
```bash
# 1. 현재 상태 백업
git stash push -m "pre-rollback-backup"

# 2. 롤백 실행
git revert [commit] --no-edit

# 3. CI 검증
make check

# 4. 성공 시 커밋
git push
```

## Phase 4: 롤백 검증

### 검증 체크리스트
```bash
# CI 재실행
make check

# Health 체크
curl -s http://localhost:8010/health

# 특정 테스트
pytest tests/ -v --tb=short
```

## Phase 5: 포스트모템

롤백 완료 후 기록:

```yaml
rollback_record:
  timestamp: "[ISO8601]"
  trigger: "[CI_FAIL | HEALTH_FAIL | USER_REQUEST]"

  before:
    commit: "[롤백 전 HEAD]"
    status: "[BROKEN | DEGRADED]"

  after:
    commit: "[롤백 후 HEAD]"
    status: "[HEALTHY]"

  strategy: "[REVERT | RESET | BRANCH]"

  changes_reverted:
    commits: 0
    files: 0
    lines_added: 0
    lines_removed: 0

  verification:
    ci_passed: true
    health_check: true
    manual_test: true

  root_cause: "[원인 요약]"
  prevention: "[재발 방지책]"

  evidence:
    - "[로그/스크린샷]"

```

## 출력 형식

```yaml
rollback_plan:
  timestamp: "[ISO8601]"
  trigger: "$ARGUMENTS"

  current_state:
    head: "[현재 HEAD]"
    status: "[HEALTHY | BROKEN]"
    ci_status: "[PASS | FAIL]"

  rollback_target:
    commit: "[대상 커밋]"
    reason: "[선택 이유]"
    age: "[며칠 전]"

  impact_analysis:
    commits_to_revert: 0
    files_affected: 0
    risk_level: "[LOW | MEDIUM | HIGH]"

  strategy:
    recommended: "[REVERT | RESET | BRANCH]"
    command: "[실행 명령어]"

  pre_checks:
    - status: "[PASS | FAIL]"

      check: "[체크 항목]"

  decision: "[PROCEED | ABORT | ASK_COMMANDER]"
```

## 사용 예시

```
/rollback                    # 롤백 필요성 분석
/rollback HEAD~1             # 직전 커밋 롤백
/rollback [commit_hash]      # 특정 커밋으로 롤백
/rollback --dry-run          # 시뮬레이션만
/rollback --force            # 확인 없이 실행 (위험)
```

## 안전 규칙

1. **DRY_RUN 먼저**: 항상 시뮬레이션 후 실행
2. **백업 필수**: stash 또는 브랜치로 현재 상태 보존
3. **CI 검증**: 롤백 후 반드시 CI 통과 확인
4. **기록 남기기**: 롤백 사유와 결과 문서화
5. **Force Push 금지**: main 브랜치 force push 절대 금지

---

*"善은 복구 능력에서 나온다" - Rollback v1.0 (善 Pillar)*
