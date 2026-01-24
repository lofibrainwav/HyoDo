---
description: "Evidence 번들 생성 (永 - 기록)"
allowed-tools: Bash(git:*), Read, Write
impact: MEDIUM
tags: [evidence, documentation, audit, eternity]
---

# Evidence 번들 생성

$ARGUMENTS 작업의 Evidence를 기록합니다.

## Evidence 규칙 (할루시네이션 방지)

모든 주장/수정은 최소 1개 이상 근거가 필요:
- 파일 경로 (코드/문서)
- 실행 로그 (명령어 포함)
- CI 로그 (워크플로우 결과)
- 기존 패턴 (유사 파일)

**"~같다/추정" 표현 금지. 모르면 검사 후 진행.**

## Evidence 수집

1. **변경 파일 목록**:

```bash
git diff --name-only
```

2. **커밋 해시**:

```bash
git log -1 --format="%H"
```

3. **실행 커맨드 + 결과**:
- 실행한 명령어
- 출력 요약

4. **롤백 경로**:

```bash
git revert [commit]
# 또는
git reset --hard [commit]
```

## Definition of Done

- 眞: 구현 파일 + 실행 로그 1개
- 善: CI(Trinity Gate) PASS
- 美: 문서 1개 + 사용 예시 1개
- 孝: 원샷 실행 + 실패 시 명확 메시지
- 永: Evidence(sha256/manifest) + Seal Tag

## 출력 형식

```yaml
evidence_bundle:
  task: "$ARGUMENTS"
  commit: [hash]
  files_changed:
    - [파일1]
    - [파일2]

  commands_executed:
    - cmd: [명령어]

      result: [PASS|FAIL]
  rollback: "git revert [hash]"
  verified_by: [Pyright|Ruff|pytest]
```
