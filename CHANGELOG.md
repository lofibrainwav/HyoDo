# Changelog

All notable changes to HyoDo (孝道) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.1] - 2026-01-29

### Added

- **hyodo Python package** - PyPI 배포용 패키지 생성
  - `calculate_trinity_score()` - Trinity Score 계산 함수
  - `should_auto_approve()` - 자동 승인 판단 함수
  - `TRINITY_WEIGHTS` - 5기둥 가중치 상수
  - `py.typed` - 타입 힌트 지원

### Changed

- **README.md** - 완전한 영문 문서화
  - Five Pillars 설명
  - Quick Start 가이드
  - Features 및 Project Structure
- **CONTRIBUTING.md** - 기여 가이드라인 정립
  - merge conflict 해결
  - 개발 프로세스 명확화

### Fixed

- CONTRIBUTING.md merge conflict 해결

## [3.0.0-ultrawork] - 2026-01-24

### Added

- **오호대장군 (五虎大將軍)** - Ollama 기반 FREE 티어 디버깅 군단
  - 관우 (關羽) - qwen2.5-coder:7b - 코드 리뷰
  - 장비 (張飛) - deepseek-r1:7b - 버그 추적
  - 조운 (趙雲) - qwen3:8b - 테스트 생성
  - 마초 (馬超) - codestral:latest - 빠른 코드 생성
  - 황충 (黃忠) - qwen3-vl:latest - UI 분석

- **훅 시스템**
  - `cost_check` (pre_tool) - 비용 티어 체크
  - `safety_gate` (pre_tool) - 이순신 안전 게이트
  - `ollama_debug` (on_error) - 에러 시 자동 디버깅
  - `evidence_log` (post_tool) - 결정 증거 기록
  - `metrics_emit` (post_tool) - 메트릭 수집

- **새로운 커맨드**
  - `/ultrawork` - 병렬 작업 실행
  - `/multiplatform` - 멀티플랫폼 라우팅

### Changed

- 토큰 버닝 최적화 50-70% 절감

## [2.0.0-sejong] - 2026-01-24

### Added

- **세종대왕의 정신** - 삼국지 전략가에서 조선 위인으로 마이그레이션
  - 장영실 (蔣英實) - 眞 Sword ⚔️
  - 이순신 (李舜臣) - 善 Shield 🛡️
  - 신사임당 (申師任堂) - 美 Bridge 🌉

- **Chancellor V3** - CostAwareRouter + KeyTriggerRouter 연동
- **十一臟腑** - 11 Organs 헬스체크 시스템
- 비용 최적화 40% 절감 라우팅

- **새로운 커맨드**
  - `/chancellor-v3` - Chancellor V3 라우팅 시스템 제어
  - `/organs` - 十一臟腑 건강 상태 체크
  - `/cost-estimate` - 작업 비용 사전 예측
  - `/routing` - KeyTriggerRouter 분석

### Changed

- 전략가 마이그레이션:
  - 제갈량 → 장영실 (眞)
  - 사마의 → 이순신 (善)
  - 주유 → 신사임당 (美)

## [1.0.0] - 2026-01-24

### Added

- Initial release
- 眞善美孝永 철학 기반 에이전트 오케스트레이션
- Trinity Score 시스템
- 4-Gate CI Protocol
- 기본 커맨드: `/trinity`, `/strategist`, `/check`, `/preflight`, `/evidence`, `/rollback`, `/ssot`
- 에이전트: `trinity-guardian`, `quality-gate`
- 스킬: `trinity-score-calculator`, `strategy-engine`, `philosophy-guide`, `kingdom-navigator`

---

*"세종대왕의 정신: 장영실의 정밀함, 이순신의 수호, 신사임당의 예술"*
