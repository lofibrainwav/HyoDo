# 📥 옵시디언 플러그인 수동 설치 가이드

**작성일**: 2025-12-16  
**상태**: ✅ 자동 설치 실패, 수동 설치 필요  
**목적**: 필수 플러그인 수동 설치 방법

---

## ⚠️ 자동 설치 실패 원인

- GitHub API rate limit (403 에러)
- 직접 다운로드 URL 404 에러
- **해결**: Obsidian 앱에서 수동 설치 필요

---

## 📋 설치할 플러그인 (2개)

### 최우선 (즉시 설치)

1. **obsidian-git** - Git 자동 백업 필수
2. **dataview** - Trinity 대시보드 필수

---

## 🛠️ 수동 설치 방법

### 방법 1: Obsidian 앱에서 설치 (권장)

#### 1단계: Obsidian 앱 열기

```bash
# macOS
open -a Obsidian /Users/brnestrm/AFO/docs
```

또는:
1. Obsidian 앱 실행
2. "Open folder as vault" 선택
3. `/Users/brnestrm/AFO/docs` 선택

#### 2단계: Community Plugins 활성화

1. **Settings 열기**
   - 왼쪽 하단 톱니바퀴 아이콘 클릭
   - 또는 `Cmd + ,` (macOS)

2. **Community plugins 활성화**
   - Settings → Community plugins
   - "Turn off Safe Mode" 또는 "Turn on community plugins" 클릭

#### 3단계: 플러그인 설치

**obsidian-git 설치**:
1. "Browse" 버튼 클릭
2. 검색창에 `obsidian-git` 입력
3. "Obsidian Git" 선택
4. "Install" 버튼 클릭
5. "Enable" 버튼 클릭

**dataview 설치**:
1. "Browse" 버튼 클릭
2. 검색창에 `dataview` 입력
3. "Dataview" 선택
4. "Install" 버튼 클릭
5. "Enable" 버튼 클릭

#### 4단계: Git 설정

1. Settings → Obsidian Git
2. **Auto backup**: ON
   - Vault backup interval: `10` (분)
3. **Auto pull**: ON
   - Auto pull interval: `5` (분)
4. **Commit message**: `vault backup: {{date}}`

---

### 방법 2: 웹에서 설치 (대안)

1. **Obsidian 플러그인 마켓플레이스 접속**
   - https://obsidian.md/plugins

2. **플러그인 검색 및 설치**
   - `obsidian-git` 검색
   - `dataview` 검색
   - 각 플러그인의 "Install" 버튼 클릭

---

## ✅ 설치 확인

### 명령어로 확인

```bash
# 플러그인 디렉토리 확인
ls -la /Users/brnestrm/AFO/docs/.obsidian/plugins/

# 필수 파일 확인
for plugin in obsidian-git dataview; do
    echo "=== $plugin ==="
    ls -la /Users/brnestrm/AFO/docs/.obsidian/plugins/$plugin/ | grep -E "(main.js|manifest.json)"
done
```

### Obsidian 앱에서 확인

1. Settings → Community plugins
2. "Installed plugins" 섹션 확인
3. 다음 플러그인이 보이는지 확인:
   - ✅ Obsidian Git
   - ✅ Dataview

---

## 🔧 설치 후 설정

### Git 설정 확인

설치 후 자동으로 다음 설정이 적용됩니다:
- `plugins/obsidian-git/data.json`

**수동 확인**:
1. Settings → Obsidian Git
2. Auto backup: ON (10분)
3. Auto pull: ON (5분)

### Dataview 설정 확인

1. Settings → Dataview
2. Enable JavaScript Queries: ON
3. Enable Inline Queries: ON

---

## 🧪 기능 테스트

### Git 자동 백업 테스트

1. 노트 하나 수정
2. 10분 대기 (또는 수동 커밋: `Cmd+Shift+K`)
3. Git 로그 확인:
   ```bash
   cd /Users/brnestrm/AFO/docs
   git log --oneline -5
   ```

### Dataview 쿼리 테스트

1. 새 노트 생성
2. 다음 쿼리 붙여넣기:
   ````markdown
   ```dataview
   TABLE file.mtime
   FROM "afo"
   WHERE file.name =~ "SERVICE_OPTIMIZATION"
   SORT file.mtime DESC
   LIMIT 5
   ```
   ````
3. Reading View로 확인 (자동으로 문서 목록 표시)

---

## 📝 설치 체크리스트

- [ ] Obsidian 앱 열기
- [ ] Community plugins 활성화
- [ ] obsidian-git 설치 및 활성화
- [ ] dataview 설치 및 활성화
- [ ] Git 설정 확인 (Auto backup: 10분)
- [ ] Dataview 설정 확인
- [ ] Git 자동 백업 테스트
- [ ] Dataview 쿼리 테스트

---

## 🔄 문제 해결

### 플러그인이 보이지 않을 때

1. **Obsidian 재시작**
   ```bash
   killall Obsidian
   open -a Obsidian /Users/brnestrm/AFO/docs
   ```

2. **플러그인 디렉토리 확인**
   ```bash
   ls -la /Users/brnestrm/AFO/docs/.obsidian/plugins/
   ```

3. **필수 파일 확인**
   - 각 플러그인 디렉토리에 `main.js`, `manifest.json` 파일이 있어야 함

### Git 백업이 작동하지 않을 때

1. **Git 저장소 확인**
   ```bash
   cd /Users/brnestrm/AFO/docs
   git status
   ```

2. **Git 설정 확인**
   - Settings → Obsidian Git
   - Auto backup: ON 확인

3. **수동 커밋 테스트**
   - `Cmd+Shift+K` (Git 커밋)

### Dataview 쿼리가 작동하지 않을 때

1. **플러그인 활성화 확인**
   - Settings → Community plugins
   - Dataview: Enable 확인

2. **Reading View로 전환**
   - `Cmd+E` 또는 우측 상단 아이콘

3. **쿼리 문법 확인**
   - Dataview 문서 참고: https://blacksmithgu.github.io/obsidian-dataview/

---

## 📚 참고 문서

- [빠른 시작 가이드](../OBSIDIAN_QUICK_START.md)
- [플러그인 최적화 리포트](OBSIDIAN_PLUGINS_OPTIMIZATION_COMPLETE.md)
- [설정 완료 리포트](OBSIDIAN_SETUP_COMPLETE.md)

---

**상태**: ⏳ 수동 설치 필요  
**다음 단계**: Obsidian 앱에서 플러그인 설치

