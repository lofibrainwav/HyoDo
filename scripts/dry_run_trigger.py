#!/usr/bin/env python3
"""
DRY_RUN 자동 트리거 스크립트

고위험 변경 감지 시 DRY_RUN 모드를 자동으로 활성화합니다.

고위험 변경 기준:
- 외부 API 엔드포인트 추가
- 데이터베이스 스키마 변경
- 인증/권한 로직 수정
- LOCK.md 항목 관련 코드 변경
"""

import subprocess
import sys

# 고위험 패턴 정의
HIGH_RISK_PATTERNS = [
    # 외부 API
    ("requests.post", "외부 API POST 호출"),
    ("requests.put", "외부 API PUT 호출"),
    ("requests.delete", "외부 API DELETE 호출"),
    ("httpx.post", "외부 API POST 호출"),
    ("aiohttp.ClientSession", "비동기 HTTP 클라이언트"),
    # DB 스키마
    ("ALTER TABLE", "데이터베이스 스키마 변경"),  # nosec
    ("DROP TABLE", "테이블 삭제"),  # nosec
    ("CREATE TABLE", "테이블 생성"),  # nosec
    ("alembic.op.drop", "Alembic 마이그레이션 삭제"),
    # 인증/권한
    ("oauth", "OAuth 인증 변경"),
    ("jwt", "JWT 토큰 변경"),
    ("password", "비밀번호 관련 변경"),
    ("secret", "시크릿 관련 변경"),
    ("api_key", "API 키 변경"),
    # 핵심 설정
    ("PRODUCTION", "프로덕션 설정 변경"),
    ("DATABASE_URL", "데이터베이스 URL 변경"),
]


def get_changed_files() -> list[str]:
    """Git에서 변경된 파일 목록 가져오기"""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip().split("\n") if result.stdout.strip() else []


def get_file_diff(file_path: str) -> str:
    """파일의 diff 내용 가져오기"""
    result = subprocess.run(
        ["git", "diff", "HEAD~1", "--", file_path],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout


def detect_high_risk_changes() -> list[dict]:
    """고위험 변경 감지"""
    risks = []

    changed_files = get_changed_files()

    for file_path in changed_files:
        if not file_path.endswith((".py", ".sql", ".yaml", ".yml", ".json")):
            continue

        diff = get_file_diff(file_path)

        for pattern, description in HIGH_RISK_PATTERNS:
            if pattern.lower() in diff.lower():
                risks.append(
                    {
                        "file": file_path,
                        "pattern": pattern,
                        "description": description,
                        "recommendation": "DRY_RUN 필수",
                    }
                )

    return risks


def main() -> None:
    print("🔍 고위험 변경 감지 중...")

    risks = detect_high_risk_changes()

    if not risks:
        print("✅ 고위험 변경 없음 - DRY_RUN 불필요")
        sys.exit(0)

    print(f"\n⚠️  {len(risks)}개의 고위험 변경 감지됨!")
    print("=" * 50)

    for risk in risks:
        print(f"\n📁 파일: {risk['file']}")
        print(f"   패턴: {risk['pattern']}")
        print(f"   설명: {risk['description']}")
        print(f"   권장: {risk['recommendation']}")

    print("\n" + "=" * 50)
    print("🏃 DRY_RUN 모드 활성화 필요!")
    print("   ENV=test 또는 DRY_RUN=true 설정 후 실행하세요.")

    # CI에서는 exit 1로 실패 처리
    if "--ci" in sys.argv:
        sys.exit(1)


if __name__ == "__main__":
    main()
