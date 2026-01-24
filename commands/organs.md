---
description: "十一臟腑 (11 Organs) 시스템 건강 상태 체크"
allowed-tools: Read, Glob, Grep, Bash(curl:*), mcp__afo-ultimate-mcp__health
impact: LOW
tags: [health, organs, infrastructure, monitoring]
---

# 十一臟腑 (11 Organs) 건강 체크

AFO Kingdom의 11개 핵심 인프라 장기 상태를 점검합니다.

## 장기 목록

```
┌─────────────────────────────────────────────────────────────┐
│                    十一臟腑 (11 Organs)                      │
│              "왕국의 생명을 유지하는 핵심 기관"               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  心 (심장)     Redis           캐시/세션 관리               │
│  肝 (간)       PostgreSQL      영구 데이터 저장              │
│  腦 (뇌)       Soul Engine     핵심 비즈니스 로직            │
│  舌 (혀)       Ollama          로컬 LLM 추론                │
│  肺 (폐)       LanceDB         벡터 검색/임베딩              │
│  眼 (눈)       Dashboard       시각화/모니터링               │
│  腎 (신장)     MCP Servers     외부 시스템 연동              │
│  耳 (귀)       Observability   로그/메트릭 수집              │
│  口 (입)       Docs            문서화 시스템                 │
│  骨 (뼈)       CI Pipeline     빌드/테스트 파이프라인         │
│  胱 (방광)     Evolution Gate  진화/마이그레이션 게이트       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 각 장기 상세

### 心 (심장) - Redis

- **역할**: 캐시, 세션, 실시간 데이터
- **체크 포인트**: 연결 상태, 메모리 사용량, 키 개수
- **위험 신호**: 연결 실패, 메모리 90% 초과

### 肝 (간) - PostgreSQL

- **역할**: 영구 데이터 저장, 트랜잭션
- **체크 포인트**: 연결 풀, 쿼리 성능, 디스크 사용량
- **위험 신호**: 연결 풀 고갈, 슬로우 쿼리

### 腦 (뇌) - Soul Engine

- **역할**: AFO 핵심 로직, Trinity Score 계산
- **체크 포인트**: API 응답, 에러율, 처리량
- **위험 신호**: 500 에러, 타임아웃

### 舌 (혀) - Ollama

- **역할**: 로컬 LLM 추론 (qwen3:8b)
- **체크 포인트**: 모델 로드 상태, GPU 메모리, 응답 시간
- **위험 신호**: 모델 미로드, OOM

### 肺 (폐) - LanceDB (Vector DB)

- **역할**: 벡터 검색, 임베딩 저장
- **체크 포인트**: 인덱스 상태, 검색 성능
- **위험 신호**: 인덱스 손상, 검색 실패

### 眼 (눈) - Dashboard

- **역할**: 시각화, 모니터링 UI
- **체크 포인트**: 빌드 상태, 접근성, 렌더링
- **위험 신호**: 빌드 실패, 504 에러

### 腎 (신장) - MCP Servers

- **역할**: 외부 시스템 연동 (9개 서버)
- **체크 포인트**: 각 서버 연결 상태
- **위험 신호**: 서버 다운, 인증 실패

### 耳 (귀) - Observability

- **역할**: 로그, 메트릭, 트레이싱 수집
- **체크 포인트**: 수집 파이프라인, 저장소 상태
- **위험 신호**: 데이터 유실, 지연

### 口 (입) - Docs

- **역할**: 문서화 시스템, SSOT 관리
- **체크 포인트**: 빌드 상태, 링크 유효성
- **위험 신호**: 깨진 링크, 빌드 실패

### 骨 (뼈) - CI Pipeline

- **역할**: 빌드, 테스트, 배포 파이프라인
- **체크 포인트**: 4-Gate (Pyright→Ruff→pytest→SBOM)
- **위험 신호**: 게이트 실패, 타임아웃

### 胱 (방광) - Evolution Gate

- **역할**: 진화/마이그레이션 관리
- **체크 포인트**: 마이그레이션 상태, 버전 일관성
- **위험 신호**: 마이그레이션 실패, 버전 충돌

---

## 출력 형식

```yaml
organs_health_report:
  timestamp: [ISO 8601]
  overall_status: [HEALTHY | DEGRADED | CRITICAL]

  organs:
    心_Redis:
      status: [UP | DOWN | DEGRADED]
      latency_ms: [응답 시간]
      details: "[상세 정보]"

    肝_PostgreSQL:
      status: [UP | DOWN | DEGRADED]
      connections: [활성/최대]
      details: "[상세 정보]"

    腦_Soul_Engine:
      status: [UP | DOWN | DEGRADED]
      error_rate: [에러율]%
      details: "[상세 정보]"

    舌_Ollama:
      status: [UP | DOWN | DEGRADED]
      model_loaded: [true/false]
      details: "[상세 정보]"

    肺_Vector_DB:
      status: [UP | DOWN | DEGRADED]
      index_count: [인덱스 수]
      details: "[상세 정보]"

    眼_Dashboard:
      status: [UP | DOWN | DEGRADED]
      build_status: [SUCCESS/FAILED]
      details: "[상세 정보]"

    腎_MCP:
      status: [UP | DOWN | DEGRADED]
      servers_up: [활성/전체]
      details: "[상세 정보]"

    耳_Observability:
      status: [UP | DOWN | DEGRADED]
      data_lag_seconds: [지연 시간]
      details: "[상세 정보]"

    口_Docs:
      status: [UP | DOWN | DEGRADED]
      broken_links: [깨진 링크 수]
      details: "[상세 정보]"

    骨_CI:
      status: [UP | DOWN | DEGRADED]
      last_run: [마지막 실행]
      details: "[상세 정보]"

    胱_Evolution_Gate:
      status: [UP | DOWN | DEGRADED]
      pending_migrations: [대기 중 마이그레이션]
      details: "[상세 정보]"

  summary:
    healthy: [정상 장기 수]
    degraded: [저하 장기 수]
    critical: [위험 장기 수]
    recommendations:
      - "[권고 사항 1]"
      - "[권고 사항 2]"
```

---

## 관련 파일

- `packages/afo-core/AFO/health/organs_truth.py`
- `packages/afo-core/AFO/health/`
