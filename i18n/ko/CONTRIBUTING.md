# HyoDo (孝道) 기여 가이드

> "세종대왕의 정신: 백성을 위한 실용적 혁신"

<p align="center">
  <a href="../../CONTRIBUTING.md">English</a> •
  <a href="../zh/CONTRIBUTING.md">中文</a> •
  <a href="../ja/CONTRIBUTING.md">日本語</a>
</p>

HyoDo 프로젝트에 기여해 주셔서 감사합니다.

## 眞善美孝永 기여 원칙

모든 기여는 다섯 기둥(五柱)에 따라 평가됩니다:

| 기둥 | 가중치 | 기여 기준 |
|------|--------|----------|
| **眞 (Truth)** | 35% | 기술적으로 정확한가? |
| **善 (Goodness)** | 35% | 안전하고 안정적인가? |
| **美 (Beauty)** | 20% | 코드가 읽기 쉬운가? |
| **孝 (Serenity)** | 8% | 사용자 경험이 좋은가? |
| **永 (Eternity)** | 2% | 장기적으로 유지 가능한가? |

## 기여 프로세스

### 1. Issue 생성

새로운 기능이나 버그 수정 전에 Issue를 먼저 생성해주세요.

### 2. Fork & Branch

```bash
git fork https://github.com/lofibrainwav/HyoDo.git
git checkout -b feature/your-feature-name
```

### 3. 개발

- 세종대왕의 정신 (장영실/이순신/신사임당) 원칙을 따르세요
- 오호대장군 (Ollama FREE 티어)을 활용하여 디버깅하세요

### 4. 테스트

```bash
# Trinity Score 확인
/trinity "your changes"

# 전략가 분석
/strategist "your changes"

# 품질 게이트
/check
```

### 5. Pull Request

- PR 제목은 명확하게 작성
- 변경 사항을 설명
- Trinity Score >= 70 필수

## 코드 스타일

- 한국어 주석 권장 (한국어 기여자)
- 세종대왕의 정신 철학 반영
- 眞善美 균형 유지

## 질문?

Issue를 통해 질문해주세요.

---

*"전략가가 지휘하고, 무장이 실행한다"*
