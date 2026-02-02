# HyoDo 3분 퀵스타트 🚀

> **"코드 품질, 이제 AI에게 맡기세요"**

## ⚡ 3단계 설치 (3분)

### 1단계: 설치 (1분)

```bash
# 대화형 설치 스크립트 실행
curl -sSL https://raw.githubusercontent.com/lofibrainwav/HyoDo/main/install_interactive.sh | bash

# 또는 수동 설치
git clone https://github.com/lofibrainwav/HyoDo.git ~/.hyodo
cd ~/.hyodo
./install_interactive.sh
```

### 2단계: API 키 설정 (1분)

```bash
# .env 파일 편집
nano ~/.hyodo/.env

# ANTHROPIC_API_KEY에 발급받은 키 입력
# 키 발급: https://console.anthropic.com/
```

### 3단계: 실행 (1분)

```bash
# Claude Code 실행
cd ~/.hyodo && claude

# 첫 명령어
/start    # 시작 가이드
/check    # 코드 품질 검사
/score    # Trinity Score 확인
```

---

## 🎯 주요 명령어 5가지

| 명령어 | 설명 | 사용 예시 |
|--------|------|-----------|
| `/start` | 시작 가이드 | `/start` |
| `/check` | 코드 품질 검사 | `/check` |
| `/score` | Trinity Score 계산 | `/score` |
| `/safe` | 보안 검사 | `/safe` |
| `/cost` | 비용 예측 | `/cost` |

---

## 📊 Trinity Score란?

HyoDo는 코드를 5가지 철학적 기준으로 평가합니다:

```
Trinity Score = 0.35×眞(진실) + 0.35×善(선함) + 0.20×美(아름다움) 
                + 0.08×孝(효) + 0.02×永(영원)
```

| 점수 | 의미 | 조치 |
|------|------|------|
| 90+ | 🟢 우수 | 자동 승인 가능 |
| 70-89 | 🟡 양호 | 검토 권장 |
| 50-69 | 🟠 개선 필요 | 수정 필요 |
| <50 | 🔴 위험 | 차단 |

---

## 🆘 문제 해결

### Claude Code가 없어요
```bash
# Claude Code 설치
npm install -g @anthropic-ai/claude-code
```

### API 키 오류
```bash
# .env 파일 확인
cat ~/.hyodo/.env | grep ANTHROPIC

# 키 형식: sk-ant-... (48자 이상)
```

### 명령어가 안 보여요
```bash
# HyoDo 디렉토리에서 실행
cd ~/.hyodo
claude
```

---

## 📚 다음 단계

- [전체 문서](README.md)
- [상세 가이드](QUICK_START.md)
- [기여 가이드](CONTRIBUTING.md)

---

**"지피지기 백전백승" - HyoDo와 함께 코드 품질을 향상시켜보세요!** ⚔️
