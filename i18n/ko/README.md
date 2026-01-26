# HyoDo (孝道)

> **Claude Code를 위한 AI 코드 품질 자동화**

<p align="center">
  <a href="../../README.md">English</a> •
  <a href="../zh/README.md">中文</a> •
  <a href="../ja/README.md">日本語</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-blueviolet" alt="Claude Code">
  <img src="https://img.shields.io/badge/비용_절감-50--70%25-green" alt="Cost Savings">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

---

## HyoDo란?

HyoDo는 Trinity Score 시스템을 사용하여 코드 품질 검사를 자동화하는 **Claude Code 플러그인**입니다:

- **문제를 조기에 발견** — 문제가 되기 전에 잡아냄
- **AI 비용 절감** — 지능형 캐싱으로 50-70% 절감
- **확신 있는 결정** — 명확한 합격/불합격 점수

---

## 30초 시작

```bash
/start              # 도움말
/check              # 코드 품질 체크
/score              # 점수 확인 (90점 이상 = 안전)
/safe               # 안전성 검사
/cost "작업 설명"   # 비용 예측
```

**끝!** 이것만 알면 됩니다.

---

## Trinity Score

HyoDo는 세 가지 차원에서 코드를 평가합니다:

| 차원 | 가중치 | 검사 항목 |
|:-----|:------:|:----------|
| **眞 진리** | 35% | 타입 안전성, 로직 정확성, 테스트 통과 |
| **善 선함** | 35% | 보안, 안정성, 에러 처리 |
| **美 아름다움** | 20% | 코드 스타일, 문서화, 가독성 |

추가로 **孝 평온 (8%)** 개발자 경험, **永 영원 (2%)** 유지보수성.

### 점수 해석

| 점수 | 상태 | 행동 |
|:----:|:----:|:-----|
| 90+ | ✅ 안전 | 바로 진행 |
| 70-89 | ⚠️ 주의 | 확인 후 진행 |
| < 70 | ❌ 위험 | 수정 필요 |

---

## 설치

### 방법 1: Git Clone
```bash
git clone https://github.com/lofibrainwav/HyoDo.git ~/.hyodo
```

### 방법 2: 원클릭 설치
```bash
curl -sSL https://raw.githubusercontent.com/lofibrainwav/HyoDo/main/install.sh | bash
```

---

## 명령어

### 심플 모드 (추천)

| 명령어 | 설명 |
|:-------|:-----|
| `/start` | 시작 가이드 |
| `/check` | 품질 검사 실행 |
| `/score` | Trinity Score 보기 |
| `/safe` | 보안 검사 |
| `/cost` | AI 비용 예측 |

### 고급 모드

| 명령어 | 설명 |
|:-------|:-----|
| `/trinity` | 상세 점수 분석 |
| `/preflight` | 커밋 전 검증 |
| `/ultrawork` | 병렬 작업 실행 |
| `/evidence` | 감사 로깅 |
| `/rollback` | 변경 취소 |

---

## 작동 방식

```
코드 → HyoDo 분석 → Trinity Score → 결정
                          │
               ┌──────────┼──────────┐
               │          │          │
            90+: 진행   70-89: 확인  <70: 중단
```

HyoDo는 로컬 AI (Ollama)를 사용하여 분석하므로 코드가 비공개로 유지되고 비용이 낮습니다.

---

## 문서

| 문서 | 설명 |
|:-----|:-----|
| [QUICK_START.md](../../QUICK_START.md) | 5분 빠른 시작 |
| [CONTRIBUTING.md](../../CONTRIBUTING.md) | 기여 가이드 |
| [ROADMAP.md](../../ROADMAP.md) | 향후 계획 |

---

## 철학

**HyoDo (孝道)**는 "평온의 길" — 개발 워크플로우에서 마찰을 줄입니다.

세종대왕 시대의 지혜에서 영감을 받아, HyoDo는 모든 결정에 세 가지 관점을 적용합니다:

- **장영실** ⚔️ — "3년 후에도 작동할까?"
- **이순신** 🛡️ — "최악의 경우는?"
- **신사임당** 🌉 — "사용자가 이해할 수 있나?"

---

## 기여하기

가이드라인은 [CONTRIBUTING.md](../../CONTRIBUTING.md)를 참조하세요.

## 라이선스

MIT - [LICENSE](../../LICENSE)

---

<p align="center">
  <em>처음이신가요? <code>/start</code>로 시작하세요!</em>
</p>
