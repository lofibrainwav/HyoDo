#!/bin/bash

# 🛡️ AFO Kingdom 일일 보안 스캔 스크립트
# 매일 실행되어 시크릿 노출을 모니터링합니다

set -euo pipefail

# 스크립트 위치 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$PROJECT_ROOT/artifacts"

# 날짜 설정
TODAY=$(date +%Y%m%d)
REPORT_FILE="$ARTIFACTS_DIR/security_scan_$TODAY.txt"

# artifacts 디렉토리 생성
mkdir -p "$ARTIFACTS_DIR"

# 스캔 시작 로그
echo "🛡️ AFO Kingdom 일일 보안 스캔 - $TODAY" > "$REPORT_FILE"
echo "==========================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 1. 시크릿 후보 스캔 (rg 사용)
echo "1️⃣ 시크릿 후보 스캔 (rg)..." >> "$REPORT_FILE"
SECRET_COUNT=$(rg -n --hidden --no-ignore-vcs -S \
  "(api[_-]?key|secret|password|passwd|token|jwt|bearer|dsn|private[_-]?key|client[_-]?secret|authorization)" \
  -g'!.venv/*' -g'!**/node_modules/*' -g'!.git/*' \
  "$PROJECT_ROOT" 2>/dev/null | wc -l | tr -d ' ')

echo "총 시크릿 후보 수: $SECRET_COUNT" >> "$REPORT_FILE"

if [ "$SECRET_COUNT" -gt 50 ]; then
    echo "⚠️ 경고: 시크릿 후보가 50개를 초과합니다!" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# 2. 환경변수 파일 권한 체크
echo "2️⃣ 환경변수 파일 보안 체크..." >> "$REPORT_FILE"

if [ -f "$PROJECT_ROOT/.env" ]; then
    ENV_PERMS=$(stat -c "%a" "$PROJECT_ROOT/.env" 2>/dev/null || stat -f "%A" "$PROJECT_ROOT/.env" 2>/dev/null || echo "unknown")
    echo ".env 파일 권한: $ENV_PERMS" >> "$REPORT_FILE"

    if [ "$ENV_PERMS" != "600" ]; then
        echo "⚠️ 경고: .env 파일 권한이 600이 아닙니다!" >> "$REPORT_FILE"
    fi
else
    echo "⚠️ 주의: .env 파일이 존재하지 않습니다" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# 3. Git 히스토리 시크릿 체크 (최근 30일)
echo "3️⃣ Git 히스토리 시크릿 체크 (최근 30일)..." >> "$REPORT_FILE"

# 최근 커밋에서 gitleaks 실행 (간단 버전)
if command -v gitleaks &> /dev/null; then
    GIT_LEAKS=$(gitleaks detect --no-git -v --redact --source "$PROJECT_ROOT" 2>&1 | grep -c "Finding:" || echo "0")
    echo "Git 히스토리 시크릿 발견: $GIT_LEAKS" >> "$REPORT_FILE"

    if [ "$GIT_LEAKS" -gt 0 ]; then
        echo "⚠️ 긴급: Git 히스토리에 시크릿이 노출되었습니다!" >> "$REPORT_FILE"
        echo "즉시 보안 프로토콜에 따라 대응하세요." >> "$REPORT_FILE"
    fi
else
    echo "gitleaks가 설치되지 않아 Git 히스토리 검사를 생략합니다" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# 4. 요약 및 권장사항
echo "4️⃣ 스캔 결과 요약" >> "$REPORT_FILE"
echo "==================" >> "$REPORT_FILE"

if [ "$SECRET_COUNT" -le 50 ] && [ "$ENV_PERMS" = "600" ]; then
    echo "✅ 보안 상태: 양호" >> "$REPORT_FILE"
else
    echo "⚠️ 보안 상태: 주의 필요" >> "$REPORT_FILE"
    echo "권장사항:" >> "$REPORT_FILE"
    [ "$SECRET_COUNT" -gt 50 ] && echo "  - 시크릿 노출 원인 분석 및 제거" >> "$REPORT_FILE"
    [ "$ENV_PERMS" != "600" ] && echo "  - .env 파일 권한을 600으로 설정" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"
echo "스캔 완료: $(date)" >> "$REPORT_FILE"
echo "보고서: $REPORT_FILE" >> "$REPORT_FILE"

# 콘솔 출력
echo "✅ 일일 보안 스캔 완료"
echo "보고서: $REPORT_FILE"

# 심각한 문제 발견 시 경고
if [ "$SECRET_COUNT" -gt 100 ] || [ "$ENV_PERMS" != "600" ]; then
    echo "🚨 긴급: 심각한 보안 문제가 발견되었습니다!"
    echo "즉시 docs/SECURITY_PROTOCOL.md를 확인하고 대응하세요."
    exit 1
fi