# 🎯 Cursor IDE 설정 가이드

**작성일**: 2025-12-17  
**상태**: ✅ 설정 완료  
**목적**: Cursor IDE 최적 설정 및 코드 품질 도구 통합

---

## 📋 생성된 설정 파일

### 1. `.cursorrules`
- 프로젝트 컨텍스트 및 코딩 스타일 규칙
- 파일 구조 가이드
- 설정 우선순위

### 2. `.cursor/settings.json`
- Cursor IDE 전용 설정
- Ruff 린터/포매터 활성화
- MyPy 타입 체크 활성화
- 저장 시 자동 포맷팅

### 3. `.vscode/settings.json`
- VS Code 호환 설정
- 동일한 Python 설정

---

## ⚙️ 주요 설정

### Python 린터
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.mypyEnabled": true,
  "python.linting.pylintEnabled": false
}
```

### 포매터
```json
{
  "python.formatting.provider": "ruff",
  "python.formatting.ruffArgs": ["--line-length=100"],
  "editor.formatOnSave": true
}
```

### 자동 수정
```json
{
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit",
    "source.fixAll": "explicit"
  }
}
```

### 파일 제외
```json
{
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true
  }
}
```

---

## 🔧 사용 방법

### 1. Cursor IDE 재시작
설정 파일을 생성한 후 Cursor IDE를 재시작하면 설정이 적용됩니다.

### 2. 저장 시 자동 포맷팅
파일을 저장하면 자동으로:
- Import 정렬
- 코드 포맷팅
- Ruff 자동 수정 가능한 이슈 수정

### 3. 타입 체크
MyPy가 실시간으로 타입 오류를 표시합니다.

---

## 📊 설정 효과

### Before
- 수동으로 Ruff 실행
- Import 정렬 수동
- 타입 체크 수동

### After
- 저장 시 자동 포맷팅
- Import 자동 정렬
- 실시간 타입 체크
- 자동 수정 가능한 이슈 즉시 수정

---

## 🎯 코딩 규칙 (`.cursorrules`)

### 타입 힌트
- Python 3.10+ 문법 사용
- `X | None` 형식 (Optional 대신)
- 모든 함수에 타입 힌트 필수

### Docstring
- Google 스타일 사용
- 모든 공개 함수에 Docstring 작성

### Import
- isort 규칙 준수
- Ruff 자동 정렬

### 라인 길이
- 최대 100자
- E501 경고 무시 (필요시)

---

## 🔍 문제 해결

### 설정이 적용되지 않는 경우
1. Cursor IDE 재시작
2. `.cursor/settings.json` 파일 확인
3. Python 확장 프로그램 설치 확인

### Ruff가 작동하지 않는 경우
```bash
pip install ruff
```

### MyPy가 작동하지 않는 경우
```bash
pip install mypy types-redis types-requests
```

---

## 📝 참고 사항

- 모든 설정은 프로젝트 루트에 저장됩니다
- `.gitignore`에 캐시 디렉토리 제외 설정됨
- 팀원들과 설정 파일 공유 가능

---

**상태**: ✅ Cursor 설정 완료  
**효과**: 자동 포맷팅 및 실시간 타입 체크 활성화

