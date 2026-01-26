# HyoDo

> **AI 코딩 도우미를 위한 자동 코드 리뷰**

<p align="center">
  <a href="../../README.md">English</a> •
  <a href="../zh/README.md">中文</a> •
  <a href="../ja/README.md">日本語</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/연동-Claude_Code-blueviolet" alt="Claude Code">
  <img src="https://img.shields.io/badge/절감-AI_비용_50--70%25-green" alt="Cost Savings">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

---

## 왜 HyoDo인가?

Claude 같은 AI 도우미로 코드를 빠르게 작성할 수 있지만, 그 코드가 **좋은 코드**인지 어떻게 알 수 있을까요?

HyoDo가 자동으로 코드 품질을 검사하고 간단한 점수를 알려줍니다:

| 점수 | 의미 | 할 일 |
|:----:|:-----|:------|
| **90+** | ✅ 통과 | 배포하세요! |
| **70-89** | ⚠️ 검토 필요 | 머지 전에 다시 확인 |
| **< 70** | ❌ 문제 발견 | 먼저 수정하세요 |

더 이상 추측하지 마세요. "내 컴퓨터에서는 되는데"는 이제 그만.

---

## 빠른 시작

[Claude Code](https://claude.ai/code) (Anthropic의 AI 코딩 도우미)를 사용한다면, 그냥 입력하세요:

```
/check
```

끝입니다. HyoDo가 코드를 분석하고 준비 여부를 알려줍니다.

### 다른 명령어

| 명령어 | 기능 |
|:-------|:-----|
| `/start` | 도움말 보기 |
| `/check` | 품질 검사 실행 |
| `/score` | 점수 확인 |
| `/safe` | 보안 문제 검사 |
| `/cost` | AI 비용 예측 |

---

## HyoDo는 무엇을 검사하나요?

HyoDo는 세 가지를 봅니다:

### 1. 작동하나요? (35%)
- 타입 에러
- 로직 버그
- 실패하는 테스트

### 2. 안전한가요? (35%)
- 보안 취약점
- 에러 처리
- 엣지 케이스

### 3. 읽기 쉬운가요? (20%)
- 코드 스타일
- 문서화
- 네이밍 규칙

추가로: 개발자 경험 (8%)과 장기 유지보수성 (2%).

---

## 설치

### Claude Code 사용자용

```bash
git clone https://github.com/lofibrainwav/HyoDo.git ~/.hyodo
```

또는 원클릭:

```bash
curl -sSL https://raw.githubusercontent.com/lofibrainwav/HyoDo/main/install.sh | bash
```

### 요구사항

- [Claude Code](https://claude.ai/code) — Anthropic 공식 코딩 도우미
- [Ollama](https://ollama.ai) (선택) — 로컬 AI 분석용 (코드 비공개 유지)

---

## 작동 방식

```
당신의 코드
    ↓
HyoDo 분석 (3가지 영역 검사)
    ↓
점수 (0-100)
    ↓
✅ 배포  /  ⚠️ 검토  /  ❌ 수정
```

모든 분석은 로컬에서 실행됩니다. 코드가 외부로 전송되지 않습니다.

---

## FAQ

**Q: HyoDo는 유료인가요?**
A: 아니요, HyoDo는 무료 오픈소스입니다 (MIT 라이선스).

**Q: 다른 AI 도우미와도 작동하나요?**
A: 현재 Claude Code에 최적화되어 있습니다. 다른 통합은 곧 지원 예정.

**Q: 어떤 언어를 지원하나요?**
A: Python, TypeScript, JavaScript 등. Claude Code가 지원하면 HyoDo도 검사할 수 있습니다.

**Q: 제 코드는 안전한가요?**
A: 네. HyoDo는 로컬에서 실행됩니다. 명시적으로 설정하지 않는 한 외부 서버로 전송되지 않습니다.

---

## 기여하기

도움을 주고 싶으신가요? [CONTRIBUTING.md](../../CONTRIBUTING.md)를 참조하세요.

## 라이선스

MIT — 원하는 대로 사용하세요.

---

<details>
<summary>이름에 대하여</summary>

**HyoDo (孝道)**는 "조화의 길"이라는 뜻입니다 — 마찰 없이 그냥 작동하는 코드를 작성하는 것.

이 프로젝트는 세종대왕 시대의 혁신에서 영감을 받아, 시대를 초월한 원칙을 현대 소프트웨어에 적용합니다:

- 장기적으로 생각하기
- 최악에 대비하기
- 단순하게 유지하기

</details>

---

<p align="center">
  <strong>처음이신가요?</strong> <code>/check</code>를 입력하고 어떻게 되는지 보세요.
</p>
