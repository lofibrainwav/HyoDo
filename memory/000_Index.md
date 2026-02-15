# 🧠 HyoDo 메모리 시스템 (Zettelkasten)

> **"메모리는 우리 시스템의 시작과 끝이다"** — HyoDo 철학

## 📁 디렉토리 구조

```
memory/
├── 000_Index.md              # 전체 색인 (MOC - Map of Content)
├── 010_Projects/             # 프로젝트별 메모
│   ├── ACTIVE/
│   ├── ARCHIVED/
│   └── TEMPLATES/
├── 020_Knowledge/            # 영구노트 (Permanent Notes)
│   ├── Architecture/
│   ├── Security/
│   ├── DevOps/
│   └── Philosophy/
├── 030_Literature/           # 문헌노트 (Literature Notes)
├── 040_Fleeting/             # 일시노트 (Fleeting Notes)
│   └── TEMP/
├── 050_Sessions/             # 세션 기록
│   └── 2026/
└── 999_Templates/            # 템플릿
```

## 🔄 메모리 워크플로우

### 1. Pre-Work Hook (작업 시작)

```bash
./scripts/pre-work-hook.sh
```

**기능**:
- 관련 메모리 검색
- 최근 세션 확인
- 활성 프로젝트 표시
- 오늘의 노트 확인

### 2. 작업 중 (In-Progress)

```bash
# 일시노트 생성
python scripts/memory_manager.py fleeting "아이디어"

# 일일 노트 업데이트
python scripts/memory_manager.py daily --activity "코드 작성" --insight "발견"
```

### 3. Post-Work Hook (작업 완료)

```bash
./scripts/post-work-hook.sh
```

**기능**:
- 세션 저장 제안
- Daily Note 업데이트 제안
- Fleeting Notes 정리 알림

## 📝 노트 유형

### 1. Fleeting Notes (일시노트)
- **위치**: `040_Fleeting/TEMP/`
- **특징**: 즉각적인 생각, 아이디어
- **처리**: 24-48시간 내 정리

### 2. Permanent Notes (영구노트)
- **위치**: `020_Knowledge/`
- **특징**: 완성된 지식
- **원칙**: 원자적, 자체 완비적, 연결성

### 3. Project Notes (프로젝트 노트)
- **위치**: `010_Projects/ACTIVE/` 또는 `ARCHIVED/`
- **특징**: 특정 프로젝트 관련 정보

### 4. Session Notes (세션 노트)
- **위치**: `050_Sessions/2026/`
- **특징**: 작업 세션 상세 기록

## 🤖 메모리 명령어

```bash
# 검색
python scripts/memory_manager.py search "키워드"

# 세션 관리
python scripts/memory_manager.py session --start --title "작업명"
python scripts/memory_manager.py session --save --outcomes "완료"

# 일시노트
python scripts/memory_manager.py fleeting "내용" --tags project/abc

# 일일 노트
python scripts/memory_manager.py daily --activity "활동" --insight "인사이트"

# 상태 확인
python scripts/memory_manager.py status
```

## 🎯 사용 원칙

1. **지피지기**: 작업 전 관련 메모리 검색
2. **원자성**: 하나의 노트 = 하나의 아이디어
3. **연결성**: 고립된 노트 만들지 않기
4. **검색가능성**: 명확한 제목과 태그

---

**버전**: 1.0  
**마지막 업데이트**: 2026-02-15

*眞善美孝永 — HyoDo의 영원한 빛*
