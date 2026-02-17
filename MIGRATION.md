# HyoDo Migration Guide

> "신사임당의 예술로 부드러운 전환"

## v2.x → v3.0.0-ultrawork

### Breaking Changes

#### 1. 전략가 이름 변경 (삼국지 → 세종대왕)

```yaml
Before (v2.x):          After (v3.x):
─────────────────────────────────────────
제갈량 (諸葛亮)    →    장영실 (蔣英實)    眞 Sword ⚔️
사마의 (司馬懿)    →    이순신 (李舜臣)    善 Shield 🛡️
주유   (周瑜)      →    신사임당 (申師任堂) 美 Bridge 🌉
```

**마이그레이션 방법:**
```bash
# 코드에서 전략가 이름 변경
sed -i 's/jang_yeong_sil/jang_yeong_sil/g' your_code.py
sed -i 's/yi_sun_sin/yi_sun_sin/g' your_code.py
sed -i 's/shin_saimdang/shin_saimdang/g' your_code.py
```

#### 2. 훅 시스템 추가

v3.0.0부터 훅이 기본 활성화됩니다.

```yaml
# plugin.json 변경
Before:
  "hooks": false

After:
  "hooks": true
```

#### 3. 오호대장군 추가

새로운 FREE 티어 디버깅 시스템:

```yaml
generals:
  - 관우 (qwen2.5-coder:7b)
  - 장비 (deepseek-r1:7b)
  - 조운 (qwen3:8b)
  - 마초 (codestral:latest)
  - 황충 (qwen3-vl:latest)
```

---

## v1.x → v2.0.0-sejong

### Breaking Changes

#### 1. Trinity Score 공식 변경

```yaml
Before (v1.x):
  Trinity Score = (眞 + 善 + 美) / 3

After (v2.x):
  Trinity Score = (眞 × 0.35) + (善 × 0.35) + (美 × 0.20) + (孝 × 0.08) + (永 × 0.02)

Current (v4):
  Trinity Score = (眞 × 0.18) + (善 × 0.18) + (美 × 0.12) + (孝 × 0.40) + (永 × 0.12)
```

#### 2. 커맨드 추가

```bash
# 새로운 커맨드
/chancellor-v3    # Chancellor V3 라우팅
/organs           # 十一臟腑 헬스체크
/cost-estimate    # 비용 예측
/routing          # KeyTriggerRouter 분석
```

---

## 호환성 매트릭스

| HyoDo Version | Claude Code | Node.js | Python |
|---------------|-------------|---------|--------|
| 3.0.x         | >= 1.0.0    | >= 18   | >= 3.11 |
| 2.0.x         | >= 1.0.0    | >= 16   | >= 3.10 |
| 1.0.x         | >= 1.0.0    | >= 14   | >= 3.9 |

---

## 롤백 절차

문제 발생 시 이전 버전으로 롤백:

```bash
# Git 태그로 롤백
git checkout v2.0.0-sejong

# 또는 plugin.json 버전 변경
"version": "2.0.0-sejong"
```

---

## 지원

- [GitHub Issues](https://github.com/lofibrainwav/HyoDo/issues)
- [CHANGELOG.md](CHANGELOG.md)

---

*"이순신의 수호: 안전한 마이그레이션"*
