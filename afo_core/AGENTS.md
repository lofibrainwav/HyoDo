# 🏹 AFO Backend Core — agents.md (afo-core)

이 문서는 루트 `AGENTS.md`의 하위 규칙이다. 충돌 시 **루트 규칙이 우선**한다.

---

## 0) Scope (이 폴더의 책임)

- FastAPI 기반 API/라우팅, 도메인 로직, 데이터/스키마, 검증(타입/테스트), 에러 처리
- "라우터는 얇게, 도메인 로직은 두껍게"를 원칙으로 한다.

---

## 1) SSOT (이 폴더에서 최우선으로 보는 근거)

에이전트는 작업 전 아래 파일의 **존재 여부를 확인하고** 존재하는 것만 읽는다.

- `./packages/afo-core/README.md`
- `./packages/afo-core/pyproject.toml`
- `./Makefile` (루트)
- `./packages/afo-core/scripts/` (존재 시)
- 루트: `./AGENTS.md`, `./docs/AFO_ROYAL_LIBRARY.md`, `./docs/AFO_CHANCELLOR_GRAPH_SPEC.md`, `./docs/AFO_FINAL_SSOT.md` (최우선 근거)

---

## 2) Pillar Focus (5기둥 적용 포인트)

- 眞: 타입/검증/테스트/에러 처리(명확한 HTTP 오류)
- 善: 보안/PII/키 노출 0, 안전한 디폴트, 비용 폭증 방지
- 美: 레이어 분리, 일관된 라우팅/서비스 구조, 중복 제거
- 孝: 운영 마찰 최소(디버그 편의, 실패 시 복구 쉬움)
- 永: 재현 가능한 테스트/결정 기록(변경 근거/커맨드)

---

## 3) Command Resolution (커맨드 추측 금지: 자동 탐색 규칙)

이 폴더에서 실행할 커맨드는 "가정"하지 않는다. 아래 순서로 **repo에서 스스로 찾는다**.

### A) 발견(Discovery) — 읽기 전용

1) `./Makefile` (루트) 존재 여부 확인  
2) `./packages/afo-core/pyproject.toml` 존재 여부 확인  
3) `./packages/afo-core/scripts/` 존재 여부 확인  
4) 루트의 CI 정의(`.github/workflows/`)가 이 패키지를 어떻게 검사하는지 확인

### B) 선택(Selection) — 존재하는 경로만 사용

- **Makefile이 있으면 Makefile 타겟을 최우선**으로 사용한다.
  - 예: `make lint`, `make type-check`, `make test`
- Makefile이 없으면 `scripts/`의 실행 스크립트를 사용한다.
- 둘 다 없으면 `pyproject.toml`에 정의된 툴(테스트/린트/타입체크)을 확인해 그 방식대로 실행한다.
- 어떤 경우든 **새 도구 도입(uv/poetry/ruff 등) 금지**: 이미 repo에 있는 방식만 사용.

### C) 실제 커맨드 예시 (repo 확인 후 사용)

- Lint: `make lint` 또는 `ruff check packages/afo-core --fix`
- Type-check: `make type-check` 또는 `mypy packages/afo-core`
- Test: `make test` 또는 `pytest packages/afo-core/tests -v`
- Build: `pip install -e ".[dev]"` (pyproject.toml 기반)

---

## 4) Backend Golden Rules (API/DB/에러 처리)

### A) API 레이어

- 라우터(HTTP)는 "입력 검증 + 호출 + 응답"만 담당한다.
- 비즈니스 로직은 서비스/도메인 레이어로 이동한다.
- 예외 처리:
  - 4xx/5xx를 명확히 구분한다.
  - 내부 예외를 그대로 노출하지 않는다(민감정보/스택트레이스 금지).

### B) 타입/검증(眞)

- 입력/출력은 가능한 한 명시적 스키마(예: Pydantic)를 사용한다.
- 런타임 검증이 필요한 구간은 "명시적으로" 넣는다(조용히 실패 금지).

### C) DB/데이터(善+孝)

- 데이터 손상/비가역 변경은 **ASK_COMMANDER** 기본.
- 마이그레이션/스키마 변경은:
  - DRY_RUN 가능하면 선행
  - 롤백 전략 필수(되돌리는 방법을 함께 제시)
- 쿼리/트랜잭션은 "일관성" 우선. 성능 최적화는 측정 근거 없으면 금지.

---

## 5) DRY_RUN Policy (위험 작업은 선 시뮬)

다음 중 하나라도 해당하면 반드시 DRY_RUN 선행 + ASK 필요:

- 스키마 변경/데이터 삭제/대량 업데이트
- 인증/권한/보안 관련 변경
- 비용/리소스 사용량이 큰 배치/인덱싱 작업

---

## 6) Quality Gates (이 폴더의 완료 기준)

에이전트는 아래 게이트를 "repo에 정의된 방식"으로 실행하고, 실제 실행 커맨드를 기록한다.

### 최소 게이트(존재하는 것만)

- Lint/Format: `make lint` 또는 `ruff check` + `ruff format`
- Type-check: `make type-check` 또는 `mypy`
- Tests: `make test` 또는 `pytest`
- (해당 시) Build / container health / API startup smoke test

---

## 7) Logging & Secrets (절대 규칙)

- 토큰/키/비밀번호/쿠키/세션/개인정보를 로그에 남기지 않는다.
- 프롬프트/컨텍스트/에러 로그는 **redaction**(민감정보 마스킹) 원칙.
- 디버그 로그는 "필요 최소"로만.

---

## 8) Output Contract (보고 포맷)

작업 결과는 반드시 아래 JSON 요약을 포함한다.

```json
{
  "decision": "AUTO_RUN | ASK_COMMANDER | BLOCK",
  "risk_score": 0,
  "trinity_score": 0,
  "evidence": ["..."],
  "files_changed": ["..."],
  "checks_ran": ["..."],
  "rollback_plan": ["..."]
}
```

---

## 9) Security Checklist (보안 체크리스트 - 야전교범)

> **"측정 도구를 의심하라"** — AFO Royal Library Principle #21

### 🚨 지피지기: gh CLI dependabot 명령어

**중요**: gh CLI의 core 명령어에는 dependabot이 없습니다. **확장(Extension)**으로 제공됩니다.

```bash
# ❌ 잘못된 인식
gh dependabot  # 명령어 없음 에러

# ✅ 올바른 해결책 (지피지기)
# 1. 왜 없는지 이해: gh CLI는 경량 core + 확장 아키텍처
# 2. 확장 설치: 
gh extension install kumak1/gh-dependabot-alerts

# 3. 사용
gh dependabot-alerts --repo owner/repo
```

### 🛠️ 필수 보안 도구

#### 1. 로컬 스캐닝: pip-audit
```bash
pip install pip-audit
pip-audit --desc --format=table
```

#### 2. GitHub 통합: gh dependabot-alerts
```bash
# 설치
gh extension install kumak1/gh-dependabot-alerts

# 사용
gh dependabot-alerts --repo owner/repo --severity critical,high
```

#### 3. 통합 스캐너 (AFO Kingdom 표준)
```bash
python afo_core/scripts/security_scanner.py --repo owner/repo
```

### 📋 보안 체크리스트

#### 매일 (Daily)
- [ ] `python afo_core/scripts/security_scanner.py` 실행
- [ ] Critical 취약점 존재 여부 확인

#### 매주 (Weekly)
- [ ] `gh dependabot-alerts --repo owner/repo` 실행
- [ ] High 이상 취약점 목록 검토
- [ ] 패치 가능한 취약점 업데이트

#### 보안 이슈 발견 시
1. **즉시 BLOCK**: Critical 취약점은 즉시 보고
2. **DRY_RUN**: 패치 전 영향도 분석
3. **지식 공유**: mem/qmd에 기록, 다른 승상들에게 알림
4. **문서화**: `docs/SECURITY_SCANNING.md` 참조

### 📚 참고 자료

- **상세 문서**: `docs/SECURITY_SCANNING.md`
- **지식 저장소**: mem ("gh CLI dependabot 명령어 부재 이유")
- **통합 스크립트**: `afo_core/scripts/security_scanner.py`

---

# End of ./packages/afo-core/agents.md
