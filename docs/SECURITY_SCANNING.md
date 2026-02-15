# AFO Kingdom 보안 스캐닝 표준 프로세스

> **"지피지기 백전불태"** — 보안 취약점을 알아야 왕국을 지킨다

## 🎯 개요

AFO Kingdom의 보안 스캐닝은 **"측정 도구를 의심하라"**는 원칙에 따라,
도구의 한계를 인식하고 다층적 접근을 통해 취약점을 탐지합니다.

## 🚨 중요 발견: gh CLI dependabot 명령어

### 왜 dependabot 명령어가 없는가?

**gh CLI는 확장(Extension) 아키텍처를 사용합니다.**

```
gh CLI 구조:
├── Core Commands (내장 명령어)
│   ├── gh repo
│   ├── gh pr
│   ├── gh issue
│   └── ...
│
└── Extensions (확장 명령어)
    ├── gh copilot
    ├── gh dependabot-alerts  ← 여기에 dependabot이 있음!
    └── ...
```

### 해결책

```bash
# 1. dependabot-alerts 확장 설치
gh extension install kumak1/gh-dependabot-alerts

# 2. 설치 확인
gh extension list
# 출력: gh dependabot-alerts  kumak1/gh-dependabot-alerts  v0.2.6

# 3. 사용
gh dependabot-alerts --repo owner/repo --severity critical
```

## 🛠️ 표준 보안 스캐닝 도구

### 1. 로컬 스캐닝: pip-audit

Python 패키지의 알려진 취약점을 스캔합니다.

```bash
# 설치
pip install pip-audit

# 기본 사용법
pip-audit --desc --format=table

# requirements.txt 스캔
pip-audit --requirement requirements.txt

# 자동 수정 시도
pip-audit --fix
```

### 2. GitHub 통합: gh dependabot-alerts

GitHub Security Advisories와 연동하여 저장소 수준의 취약점을 확인합니다.

```bash
# Critical/High 취약점 조회
gh dependabot-alerts --repo owner/repo --severity critical,high

# 특정 에코시스템 필터링
gh dependabot-alerts --repo owner/repo --ecosystem pip

# JSON 형식으로 출력
gh dependabot-alerts --repo owner/repo --format json
```

**주의**: gh CLI 인증이 필요합니다 (`gh auth login`)

### 3. 통합 스캐너: security_scanner.py

AFO Kingdom에서 개발한 통합 보안 스캐닝 도구입니다.

```bash
# 사용법
python afo_core/scripts/security_scanner.py --repo owner/repo

# 옵션
--repo REPO              GitHub 저장소 (owner/repo)
--req REQUIREMENTS       requirements.txt 경로
--severity SEVERITY      심각도 필터 (기본: high,critical)
--format {table,json}    출력 형식
--setup                  필요한 도구 자동 설치
```

#### 기능

- ✅ pip-audit와 gh dependabot-alerts 통합
- ✅ 자동 설치 및 설정 확인
- ✅ 심각도별 그룹화된 보고서
- ✅ JSON/Table 이중 출력 형식
- ✅ Critical/High 취약점 발견시 exit code 1 반환

## 📋 보안 체크리스트

### 매일 (Daily)

- [ ] `python security_scanner.py`로 로컬 스캔
- [ ] Critical 취약점 존재 여부 확인

### 매주 (Weekly)

- [ ] `gh dependabot-alerts --repo owner/repo`로 원격 스캔
- [ ] High 이상 취약점 목록 검토
- [ ] 패치 가능한 취약점 업데이트

### 매월 (Monthly)

- [ ] 전체 보안 감사 보고서 생성
- [ ] 새로운 취약점 트렌드 분석
- [ ] 보안 정책 업데이트 검토

## 🔧 설정 가이드

### 초기 설정 (한 번만)

```bash
# 1. gh CLI 설치 확인
gh --version

# 2. gh CLI 인증
gh auth login

# 3. dependabot-alerts 확장 설치
gh extension install kumak1/gh-dependabot-alerts

# 4. pip-audit 설치
pip install pip-audit

# 5. 설치 확인
python afo_core/scripts/security_scanner.py --setup
```

### CI/CD 통합

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # 매일 자정

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Security Scanner
        run: |
          pip install pip-audit
          python afo_core/scripts/security_scanner.py --repo ${{ github.repository }}
```

## 🎓 메타인지: "측정 도구를 의심하라"

### 사례: gh CLI dependabot 명령어

**문제**: `gh dependabot` 명령어가 없음

**잘못된 접근**:
```bash
# ❌ 단순히 대안을 찾기만 함
"gh에 dependabot 명령어가 없으니 pip-audit를 쓰자"
```

**올바른 접근 (지피지기)**:
```bash
# ✅ 왜 없는지 이해
"gh CLI는 확장 아키텍처를 사용한다"
"core 명령어가 아니라 extension으로 제공된다"

# ✅ 해결책 구현
gh extension install kumak1/gh-dependabot-alerts

# ✅ 지식 공유
# - mem에 저장
# - qmd에 문서화
# - AGENTS.md에 체크리스트 추가
# - 다른 승상들에게 알림
```

## 📚 참고 자료

- [gh CLI Extensions](https://cli.github.com/manual/gh_extension)
- [pip-audit Documentation](https://pypi.org/project/pip-audit/)
- [GitHub Security Advisories](https://github.com/advisories)
- [AFO Kingdom 보안 정책](../SECURITY.md)

## ⚠️ 주의사항

1. **인증 필요**: gh dependabot-alerts는 `gh auth login` 필요
2. **권한 필요**: 저장소에 대한 Security 탭 접근 권한 필요
3. **비공개 저장소**: 비공개 저장소는 추가 권한 설정 필요
4. **속도 제한**: GitHub API 속도 제한에 유의

---

**문서 버전**: 1.0  
**마지막 업데이트**: 2026-02-15  
**작성자**: 승상 Claude Code (자룡)  
**지피지기 원칙**: 측정 도구를 의심하고, 이해하고, 공유하라

---

*眞善美孝永 — 왕국의 영원한 빛*
