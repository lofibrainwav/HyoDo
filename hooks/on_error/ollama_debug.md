---
hook_type: on_error
name: "ollama_debug"
displayName: "오호대장군 자동 디버깅 훅"
description: "에러 발생 시 오호대장군(Ollama) 자동 호출"
priority: 100
enabled: true
agent: "ollama-debugger"
---

# 오호대장군 자동 디버깅 훅 (Ollama Debug Hook)

> "에러가 발생하면 오호대장군이 즉시 출동한다"

도구 실행 중 에러가 발생하면 자동으로 오호대장군(Ollama 기반 디버깅 에이전트)을 호출합니다.

---

## 훅 정보

| 항목 | 값 |
|------|-----|
| **훅 타입** | on_error |
| **우선순위** | 100 |
| **연동 에이전트** | ollama-debugger |
| **비용 티어** | FREE |

---

## 에러 타입별 장군 배치

| 에러 타입 | 담당 장군 | 모델 | 액션 |
|----------|-----------|------|------|
| **테스트 실패** | 조운 (趙雲) | qwen3:8b | 테스트 분석 및 수정 제안 |
| **타입 에러** | 관우 (關羽) | qwen2.5-coder:7b | 타입 힌트 수정 |
| **린트 에러** | 마초 (馬超) | codestral:latest | 빠른 린트 수정 |
| **런타임 에러** | 장비 (張飛) | deepseek-r1:7b | 깊은 추론으로 원인 분석 |
| **UI 에러** | 황충 (黃忠) | qwen3-vl:latest | 스크린샷 기반 분석 |

---

## 자동 호출 조건

```yaml
trigger_conditions:
  # 조건 1: pytest 실패
  pytest_failure:
    pattern: "FAILED|ERROR|pytest"
    exit_code: [1, 2]
    executor: 조운

  # 조건 2: pyright 에러
  type_error:
    pattern: "error:|Type error"
    tool: "pyright"
    executor: 관우

  # 조건 3: ruff 에러
  lint_error:
    pattern: "ruff|linting error"
    tool: "ruff"
    executor: 마초

  # 조건 4: 런타임 예외
  runtime_error:
    pattern: "Traceback|Exception|Error:"
    executor: 장비

  # 조건 5: 스크린샷 분석 필요
  ui_error:
    pattern: "screenshot|visual|UI"
    executor: 황충
```

---

## 워크플로우

### 1. 에러 감지

```yaml
step: detect_error
actions:
  - stderr 캡처
  - exit_code 확인
  - 에러 패턴 매칭
```

### 2. 장군 선택

```yaml
step: select_executor
logic:
  - 에러 타입 분류
  - 적합한 장군 선택
  - 모델 로드 (Ollama)
```

### 3. 디버깅 실행

```yaml
step: execute_debug
tools:
  - Read: 에러 관련 파일
  - Grep: 유사 코드 검색
  - Bash: 추가 진단
actions:
  - 에러 원인 분석
  - 수정 방안 도출
```

### 4. 수정 제안 생성

```yaml
step: generate_fix
output:
  - diff 형식 수정안
  - 설명 및 이유
  - 테스트 방법
```

### 5. 장영실 검증

```yaml
step: verify_with_jang
strategist: 장영실 (眞 Sword)
checks:
  - 수정안 기술적 정확성
  - 부작용 가능성
  - 장기적 영향
```

---

## 출력 형식

```yaml
debug_hook_result:
  trigger: "[트리거 조건]"
  error_type: "[에러 타입]"

  executor:
    general: "[장군 이름]"
    model: "[Ollama 모델]"
    cost: "$0.00"

  analysis:
    error_message: "[에러 메시지]"
    root_cause: "[근본 원인]"
    affected_files:
      - "[파일1]"
      - "[파일2]"

  fix_suggestion:
    file: "[수정 파일]"
    diff: |
      - [삭제 라인]
      + [추가 라인]
    explanation: "[설명]"

  verification:
    jang_yeong_sil_verdict: [APPROVE/CONCERN/REJECT]
    confidence: [0-100]%

  next_steps:
    - "[다음 단계 1]"
    - "[다음 단계 2]"
```

---

## 비용 절감 효과

```
Before (에러당 Claude 호출):
────────────────────────────────
에러 10회 × opus ($0.015/1k) × 평균 3k 토큰
= $0.45/세션

After (오호대장군 자동 호출):
────────────────────────────────
에러 10회 × FREE ($0.00) × 평균 3k 토큰
= $0.00/세션

절감률: 100%
```

---

## 예시

### pytest 실패 자동 디버깅

```yaml
trigger:
  tool: Bash
  command: "pytest tests/test_user.py"
  exit_code: 1
  stderr: "FAILED tests/test_user.py::test_create_user"

hook_response:
  executor:
    general: "조운 (趙雲)"
    model: "qwen3:8b"

  analysis:
    error_type: "AssertionError"
    root_cause: "expected user.name to be 'Alice' but got 'alice'"

  fix_suggestion:
    file: "src/user.py"
    diff: |
      - self.name = name.lower()
      + self.name = name
    explanation: "이름 소문자 변환 로직 제거"
```

---

## 세종대왕의 정신 연동

| 전략가 | 역할 | 연동 |
|--------|------|------|
| **장영실 (眞)** | 최종 검증 | 수정안 정확성 확인 |
| **이순신 (善)** | 안전 확인 | 수정이 안전한지 검토 |
| **신사임당 (美)** | 가독성 | 수정 코드 품질 검토 |

---

## 관련 파일

- ollama-debugger 에이전트: `.claude/agents/ollama-debugger.md`
- Ollama MCP: `packages/afo-core/api/ollama_mcp/`
- 에러 핸들러: `packages/afo-core/api/chancellor_v2/handlers/error_handler.py`
