---
description: "[Simple] 현재 코드의 품질 점수 확인"
allowed-tools: Read, Glob, Grep, Bash(hyodo:*)
impact: LOW
tags: [simple, score, beginner]
mode: simple
alias: trinity
---

# /score - 품질 점수 확인

현재 변경에 대한 **리뷰 신호(review signal)** 를 보여줍니다. (Advanced: `/trinity`)

점수는 의사결정 지원입니다. 높은 점수도 위험한 변경의 자동 승인을 의미하지 않습니다.

## 사용법

Agent slash command:

```text
/score
/score "변경사항"
```

벤더 무관 CLI:

```bash
hyodo score --truth 0.9 --goodness 0.9 --beauty 0.9 --benevolence 0.9 --loyalty 0.9
```

## 점수 구성 (리뷰 가중 힌트)

| 항목 | 비중 | 의미 |
| :--- | :--- | :--- |
| 정확성 | 35% | 코드가 올바른가? |
| 안전성 | 35% | 문제가 없는가? |
| 가독성 | 20% | 읽기 쉬운가? |
| 편의성 | 8% | 쓰기 편한가? |
| 지속성 | 2% | 오래 유지되는가? |

공개 패키지 CLI의 HYOGOOK V5는 仁/眞/善/忠/美 입력으로 F/S를 계산합니다. 위 표는 초급 설명용 힌트입니다.

## 결과 예시 (The North Star Report)

```text
품질 점수: 92/100 (North Star Balance: OPTIMAL)

[眞] 정확성: 95
[善] 안전성: 90
[美] 가독성: 88
[평온] 편의성: 92
[지속] 지속성: 90

→ REVIEW_SIGNAL_STRONG (90+)
→ 사람 최종 승인 · 테스트 · 보안 리뷰 필요
```

## 점수별 행동

| 점수 | 상태 | 다음 행동 |
| :--- | :--- | :--- |
| 90+ | 강한 리뷰 신호 | 테스트/보안/사람 확인 후 진행 후보 |
| 70-89 | 주의 | 확인 후 진행 |
| 70 미만 | 위험 | 수정 필요 |

**금지 claim:** 점수만으로 자동 실행·자동 merge·자동 배포.

---

*상세 분석이 필요하면 `/trinity` 또는 `/strategist` 명령어를 사용하세요.*
