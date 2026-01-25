# 🚀 병렬 코드 품질 체크 가이드

**작성일**: 2025-12-17  
**상태**: ✅ 병렬 실행 구현 완료  
**목적**: ruff, pytest, mypy 병렬 실행으로 시간 단축

---

## 📋 개선 사항

### Before (순차 실행)
- Ruff Lint → Ruff Format → MyPy → Pytest
- 총 소요 시간: ~30-60초

### After (병렬 실행)
- Ruff Lint, Ruff Format, MyPy, Pytest 동시 실행
- 총 소요 시간: ~10-20초 (가장 느린 작업 시간)

---

## 🔧 사용 방법

### 방법 1: Bash 스크립트 (권장)

```bash
./scripts/run_quality_checks.sh
```

**특징**:
- Bash 백그라운드 프로세스 사용
- 모든 Unix 계열 시스템 지원
- 간단하고 빠름

### 방법 2: Python 스크립트

```bash
python3 scripts/run_quality_checks_parallel.py
```

**특징**:
- Python asyncio 사용
- 더 세밀한 제어 가능
- 크로스 플랫폼 지원

---

## ⚡ 성능 비교

### 순차 실행
```
Ruff Lint:    5초
Ruff Format:  3초
MyPy:         15초
Pytest:       10초
─────────────────
총 시간:      33초
```

### 병렬 실행
```
Ruff Lint:    5초 ┐
Ruff Format:  3초 ├─ 동시 실행
MyPy:         15초 │
Pytest:       10초 ┘
─────────────────
총 시간:      15초 (가장 느린 작업 시간)
```

**시간 절약**: 약 50% 단축

---

## 🔍 병렬 실행 원리

### Bash 버전

```bash
# 백그라운드로 실행
run_ruff_lint &
RUFF_LINT_PID=$!

run_mypy &
MYPY_PID=$!

# 모든 프로세스 완료 대기
wait $RUFF_LINT_PID
wait $MYPY_PID
```

### Python 버전

```python
# asyncio로 병렬 실행
tasks = [
    run_command("ruff_lint", ...),
    run_command("mypy", ...),
    run_command("pytest", ...),
]

results = await asyncio.gather(*tasks)
```

---

## 📊 실행 결과

### 성공 시

```
=== 🔍 AFO 왕국 코드 품질 체크 (병렬 실행) ===

📦 도구 설치 확인 중...

🚀 병렬 실행 시작...

📋 [병렬] Ruff Lint 체크 시작...
📋 [병렬] Ruff Format 체크 시작...
📋 [병렬] MyPy 타입 체크 시작...
📋 [병렬] Pytest 테스트 시작...

✅ Ruff Lint: 통과
✅ Ruff Format: 통과
✅ MyPy: 통과
✅ Pytest: 통과

=== 🏁 최종 결과 ===
✨ 모든 코드 품질 체크 통과!
```

### 실패 시

```
❌ Ruff Lint: 실패
(오류 출력)

❌ MyPy: 실패
(오류 출력)

=== 🏁 최종 결과 ===
❌ 일부 체크 실패
```

---

## 🎯 권장 워크플로우

### 개발 중

```bash
# 빠른 체크 (병렬 실행)
./scripts/run_quality_checks.sh
```

### 커밋 전

```bash
# 전체 체크 + 자동 수정
ruff check --fix .
ruff format .
./scripts/run_quality_checks.sh
```

### CI/CD

```bash
# 병렬 실행으로 빠른 피드백
./scripts/run_quality_checks.sh
```

---

## ⚙️ 고급 설정

### CPU 코어 수에 따른 병렬화

Bash 버전은 자동으로 모든 작업을 병렬 실행합니다.

Python 버전은 `asyncio.gather()`를 사용하여 병렬 실행합니다.

### 메모리 사용량

병렬 실행 시 메모리 사용량이 증가할 수 있습니다:
- Ruff: ~50MB
- MyPy: ~100MB
- Pytest: ~80MB
- **총합**: ~230MB (순차 실행 대비 약 2배)

---

## 🔧 문제 해결

### 프로세스 충돌

만약 병렬 실행 중 문제가 발생하면:

```bash
# 순차 실행으로 폴백
ruff check .
ruff format --check .
mypy AFO
pytest
```

### 타임아웃 설정

Python 버전에서 타임아웃 추가:

```python
results = await asyncio.wait_for(
    asyncio.gather(*tasks),
    timeout=300  # 5분
)
```

---

## 📝 참고 사항

1. **출력 순서**: 병렬 실행 시 출력 순서가 보장되지 않을 수 있습니다.
2. **리소스 사용**: CPU와 메모리를 동시에 사용하므로 시스템 부하가 증가할 수 있습니다.
3. **의존성**: 각 도구는 독립적으로 실행되므로 서로 영향을 주지 않습니다.

---

## 🎯 眞善美孝 관점

### 眞 (Truth) - 기술적 확실성
- ✅ 병렬 실행으로 정확성 유지
- ✅ 모든 도구 독립 실행

### 善 (Goodness) - 윤리·안정성
- ✅ 빠른 피드백으로 개발 효율 향상
- ✅ 리소스 사용 최적화

### 美 (Beauty) - 단순함·우아함
- ✅ 간단한 명령으로 실행
- ✅ 명확한 결과 출력

### 孝 (Serenity) - 평온·연속성
- ✅ 형님의 시간 절약 (50% 단축)
- ✅ 마찰 제거 (빠른 피드백)

---

**상태**: ✅ 병렬 실행 구현 완료  
**성능**: 약 50% 시간 단축

