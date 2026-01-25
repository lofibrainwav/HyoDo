# PH12-001 SSOT — AIRequest Refactor (2 Minimal Commits)

작성일: 2025-12-26
작성자: AFO Kingdom (승상)
대상: 대외/내부 공용 (실행 중심)

## 0) 배경 (문제 정의)

* `AIRequest`의 Optional 필드들이 기본값을 갖고 있음에도, **symlink 경로(AFO/services → ../services)** 분석 시 MyPy가 Pydantic `Field(...)` 기본값을 100% 인식하지 못해 **"Missing named argument"** 오류가 발생함.
* `services/` 경로만 분석하면 Gate는 **0 errors**로 정상임.

## 1) 목표 (Success Criteria)

* **Gate(CI)**: `services/` Strict Zone은 **항상 0 errors** 유지.
* **Truth(추적용)**: symlink 중복 분석 잡음을 제거해 **실제 기술부채만 추적**.
* 산출물: **최소 커밋 2개 + 증거 번들 3파일**.

---

## 2) 변경 계획 (2 Minimal Commits)

### Commit 1 — AIRequest 정의 이동/정리 + "파이썬 기본값" 고정
### Commit 2 — Truth exclude 적용 + 증거 번들(3파일) 생성

---

## 7) 결과 기록 (Fill After Execution)

* Commit 1 SHA: __________
* Commit 2 SHA: __________
* Gate(MyPy): ✅ 0 errors
* pytest: ✅ ____ tests passed
* Truth: ______ errors tracked (exclude 적용 후)
* Evidence Bundle: ✅ 3 files committed
