# 🚀 옵시디언 빠른 시작 가이드

## ✅ 설정 완료 항목

- [x] 플러그인 최적화 완료 (13개)
- [x] 템플릿 생성 완료
- [x] Dataview 쿼리 예시 생성 완료
- [ ] Git 설정 (obsidian-git 설치 후)
- [ ] Dataview 활성화 (dataview 설치 후)

## 📋 다음 단계

### 1. 필수 플러그인 설치 (5분)

1. **Obsidian 앱 열기**
   ```bash
   open -a Obsidian ${HOME}/AFO/docs
   ```

2. **Community Plugins 활성화**
   - Settings (Cmd+,)
   - Community plugins
   - "Turn on community plugins" 클릭

3. **필수 플러그인 설치**
   - Browse 클릭
   - 다음 플러그인 검색 및 설치:
     - `obsidian-git` (최우선)
     - `dataview` (최우선)
     - `templater-obsidian`
     - `calendar`
     - `obsidian-projects`

### 2. Git 설정 (1분)

1. Settings → Obsidian Git
2. Auto backup: ON (10분)
3. Auto pull: ON (5분)

### 3. Templater 설정 (1분)

1. Settings → Templater
2. Template folder: `templates/`
3. Trigger on new file: ON

### 4. Dataview 테스트 (1분)

1. 새 노트 생성
2. 다음 쿼리 붙여넣기:
   \`\`\`dataview
   TABLE file.mtime
   FROM "afo"
   WHERE file.name =~ "SERVICE_OPTIMIZATION"
   SORT file.mtime DESC
   LIMIT 5
   \`\`\`
3. Reading View로 확인

## 📚 생성된 파일

### 템플릿
- `templates/service-optimization-report.md`
- `templates/phase-report.md`
- `templates/daily-log.md`

### Dataview 쿼리
- `dataview-queries/trinity-dashboard.md`
- `dataview-queries/service-optimization-index.md`
- `dataview-queries/obsidian-plugins-status.md`

## 🎯 사용 예시

### 템플릿 사용
1. `Cmd+P` → "Templater: Create new note from template"
2. 템플릿 선택
3. 자동으로 변수 치환됨

### Dataview 쿼리 사용
1. 노트에 쿼리 붙여넣기
2. Reading View로 확인
3. 자동으로 문서 목록 표시

### Git 자동 백업
- 10분마다 자동 백업
- 5분마다 자동 pull
- 파일 변경 시 자동 백업

---
**상태**: ✅ 설정 완료  
**다음**: 필수 플러그인 설치
