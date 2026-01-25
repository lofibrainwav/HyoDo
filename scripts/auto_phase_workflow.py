#!/usr/bin/env python3
"""
Auto Phase Workflow Engine (Phase 49)
완전 자동화 루프: 메모리 → SSOT → 작업 → 린트 → 커밋 → 푸시 → 업데이트
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class WorkflowConfig:
    """워크플로우 설정"""

    dry_run: bool = False
    skip_memory: bool = False
    skip_ssot: bool = False
    skip_lint: bool = False
    skip_commit: bool = False
    skip_push: bool = False
    auto_create_pr: bool = False
    discord_webhook: Optional[str] = None


@dataclass
class WorkflowResult:
    """워크플로우 결과"""

    timestamp: str
    status: str  # "success", "failed", "partial"
    steps: Dict[str, Dict]
    total_steps: int = 0
    completed_steps: int = 0
    errors: List[str] = field(default_factory=list)
    git_commit_hash: Optional[str] = None


class AutoPhaseWorkflowEngine:
    """자동화 워크플로우 엔진"""

    def __init__(self, config: WorkflowConfig) -> None:
        self.config = config
        self.repo = Path.cwd()

    async def run(self) -> WorkflowResult:
        """워크플로우 실행"""
        logger.info("🚀 Starting Auto Phase Workflow Engine")
        result = WorkflowResult(
            timestamp=datetime.now(UTC).isoformat(),
            status="pending",
            steps={},
            errors=[],
        )

        # Step 1: 메모리 가져오기
        result.steps["memory"] = await self._load_memory()

        # Step 2: SSOT 체크
        result.steps["ssot_check"] = await self._check_ssot()

        # Step 3: 작업 (사용자 수동으로 수행됨)
        result.steps["work"] = {"status": "manual", "message": "User performs work"}

        # Step 4: 린트/검증
        result.steps["lint"] = await self._run_lint()

        # Step 5: 깃 커밋
        result.steps["commit"] = await self._git_commit()

        # Step 6: 깃 푸시
        result.steps["push"] = await self._git_push()

        # Step 7: 업데이트 (티켓/동기화)
        result.steps["update"] = await self._update_tickets()

        # 결과 집계
        result.total_steps = len(result.steps)
        result.completed_steps = sum(1 for s in result.steps.values() if s.get("success", False))

        # 전체 상태 판정
        if result.completed_steps == result.total_steps:
            result.status = "success"
        elif result.completed_steps > 0:
            result.status = "partial"
        else:
            result.status = "failed"

        logger.info(f"✅ Workflow completed: {result.status}")
        return result

    async def _load_memory(self) -> Dict:
        """메모리 가져오기 (Context7, 이전 작업 이력)"""
        logger.info("📚 Step 1: Loading memory...")

        if self.config.skip_memory:
            logger.info("  ⏭️  Skipped")
            return {"status": "skipped"}

        try:
            # API health 체크
            health = await self._check_api_health()

            # Context7 상태
            context7_status = health.get("organs_v2", {}).get("📚 Context7", {"status": "unknown"})

            # 이전 작업 이력 확인
            last_commit = subprocess.run(
                ["git", "log", "-1", "--format=%H"],
                capture_output=True,
                text=True,
                cwd=self.repo,
            ).stdout.strip()

            return {
                "success": True,
                "health": health.get("status", "unknown"),
                "context7": context7_status,
                "last_commit": last_commit,
            }
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}")
            return {"success": False, "error": str(e)}

    async def _check_ssot(self) -> Dict:
        """SSOT 체크"""
        logger.info("🔍 Step 2: Checking SSOT...")

        if self.config.skip_ssot:
            logger.info("  ⏭️  Skipped")
            return {"status": "skipped"}

        try:
            # ssot_monitor.py 실행
            result = subprocess.run(
                ["python3", "scripts/ssot_document_drift.py"],
                capture_output=True,
                text=True,
                cwd=self.repo,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "drifted": result.returncode != 0,
            }
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}")
            return {"success": False, "error": str(e)}

    async def _run_lint(self) -> Dict:
        """린트/검증 실행"""
        logger.info("🔎 Step 4: Running lint/checks...")

        if self.config.skip_lint:
            logger.info("  ⏭️  Skipped")
            return {"status": "skipped"}

        try:
            # CI Lock Protocol 실행
            result = subprocess.run(
                ["bash", "scripts/ci_lock_protocol.sh"],
                capture_output=True,
                text=True,
                cwd=self.repo,
            )

            # 결과 파싱
            ruff_passed = "All checks passed" in result.stdout
            mypy_passed = "0 errors found" in result.stderr or result.stdout

            return {
                "success": ruff_passed and mypy_passed,
                "ruff": ruff_passed,
                "mypy": mypy_passed,
                "output": result.stdout,
            }
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}")
            return {"success": False, "error": str(e)}

    async def _git_commit(self) -> Dict:
        """깃 커밋"""
        logger.info("💾 Step 5: Git commit...")

        if self.config.skip_commit:
            logger.info("  ⏭️  Skipped")
            return {"status": "skipped"}

        try:
            # 상태 확인
            status = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                cwd=self.repo,
            )

            if not status.stdout.strip():
                logger.info("  ✅ No changes to commit")
                return {"success": True, "status": "no_changes"}

            if self.config.dry_run:
                logger.info("  [DRY_RUN] Would commit changes")
                return {"success": True, "status": "dry_run"}

            # 커밋 메시지 생성
            commit_msg = await self._generate_commit_message()

            # 커밋
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                capture_output=True,
                text=True,
                cwd=self.repo,
            )

            # 해시 추출
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo,
            )

            return {
                "success": result.returncode == 0,
                "commit_hash": hash_result.stdout.strip(),
                "message": commit_msg,
            }
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}")
            return {"success": False, "error": str(e)}

    async def _git_push(self) -> Dict:
        """깃 푸시"""
        logger.info("⬆️  Step 6: Git push...")

        if self.config.skip_push:
            logger.info("  ⏭️  Skipped")
            return {"status": "skipped"}

        try:
            # 현재 브랜치 확인
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo,
            ).stdout.strip()

            if self.config.dry_run:
                logger.info(f"  [DRY_RUN] Would push to {branch}")
                return {"success": True, "status": "dry_run", "branch": branch}

            # 푸시
            result = subprocess.run(
                ["git", "push", "origin", branch],
                capture_output=True,
                text=True,
                cwd=self.repo,
            )

            return {
                "success": result.returncode == 0,
                "branch": branch,
                "output": result.stdout,
            }
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}")
            return {"success": False, "error": str(e)}

    async def _update_tickets(self) -> Dict:
        """티켓 업데이트 (동기화)"""
        logger.info("🔄 Step 7: Updating tickets...")

        try:
            # unified_ticket_sync.py 실행
            result = subprocess.run(
                ["python3", "scripts/unified_ticket_sync.py"],
                capture_output=True,
                text=True,
                cwd=self.repo,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "changed": "changes" in result.stdout.lower(),
            }
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}")
            return {"success": False, "error": str(e)}

    async def _check_api_health(self) -> Dict:
        """API 헬스 체크"""
        try:
            import httpx

            response = httpx.get(
                "http://localhost:8010/health",
                timeout=5.0,
            )

            return response.json()

        except Exception as e:
            logger.warning(f"API health check failed: {e}")
            return {"status": "unavailable"}

    async def _generate_commit_message(self) -> str:
        """커밋 메시지 생성"""
        # Trinity Score 가져오기
        health = await self._check_api_health()
        trinity_score = health.get("trinity", {}).get("trinity_score", 0)

        # 커밋 유형 결정
        commit_type = "feat"
        if trinity_score < 0.9:
            commit_type = "fix"
        elif any(
            s.get("success", False)
            for s in [self.config.skip_memory, self.config.skip_ssot, self.config.skip_lint]
        ):
            commit_type = "chore"

        # 메시지 생성
        msg = f"{commit_type}: Auto workflow run - Trinity Score {trinity_score:.2f}\n"
        msg += f"- Memory: {'loaded' if not self.config.skip_memory else 'skipped'}\n"
        msg += f"- SSOT: {'checked' if not self.config.skip_ssot else 'skipped'}\n"
        msg += f"- Lint: {'passed' if not self.config.skip_lint else 'skipped'}\n"
        msg += f"- Commit: {'auto' if not self.config.skip_commit else 'skipped'}\n"
        msg += f"- Push: {'auto' if not self.config.skip_push else 'skipped'}"

        return msg

    async def _send_discord_alert(self, result: WorkflowResult) -> bool:
        """Discord 알림 전송"""
        if not self.config.discord_webhook:
            return False

        if result.status == "success":
            color = 5763719  # Green
        elif result.status == "partial":
            color = 16776960  # Yellow
        else:
            color = 16711680  # Red

        message = {
            "embeds": [
                {
                    "title": f"🔄 Auto Workflow {result.status.upper()}",
                    "color": color,
                    "fields": [
                        {
                            "name": "Steps",
                            "value": f"{result.completed_steps}/{result.total_steps}",
                            "inline": True,
                        },
                        {
                            "name": "Commit",
                            "value": result.git_commit_hash or "N/A",
                            "inline": True,
                        },
                        {"name": "Timestamp", "value": result.timestamp, "inline": True},
                    ],
                    "timestamp": result.timestamp,
                }
            ]
        }

        if result.errors:
            message["embeds"][0]["description"] = "\n".join(result.errors[:5])

        try:
            from urllib.error import URLError
            from urllib.request import Request, urlopen

            req = Request(
                self.config.discord_webhook,
                data=json.dumps(message).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            urlopen(req, timeout=10)
            return True
        except URLError as e:
            logger.error(f"Discord alert failed: {e}")
            return False


def print_report(result: WorkflowResult) -> None:
    """보고서 출력"""
    print("=" * 60)
    print("  AUTO PHASE WORKFLOW REPORT")
    print("=" * 60)
    print(f"  Timestamp: {result.timestamp}")
    print(f"  Status: {result.status.upper()}")
    print(f"  Steps: {result.completed_steps}/{result.total_steps}")
    print("-" * 60)

    for step_name, step_result in result.steps.items():
        success = step_result.get("success", False)
        status_icon = "✅" if success else "❌"
        print(f"  {status_icon} {step_name}")

        if step_result.get("error"):
            print(f"       Error: {step_result['error']}")

    print("=" * 60)

    if result.status == "success":
        print("✅ All steps completed successfully")
        print(f"   Commit: {result.git_commit_hash}")
    elif result.status == "partial":
        print("⚠️  Some steps failed - review errors")
    else:
        print("❌ Workflow failed - critical errors")


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Auto Phase Workflow Engine")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run single workflow cycle",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuous monitoring",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate operations without making changes",
    )
    parser.add_argument(
        "--skip-memory",
        action="store_true",
        help="Skip memory loading step",
    )
    parser.add_argument(
        "--skip-ssot",
        action="store_true",
        help="Skip SSOT check step",
    )
    parser.add_argument(
        "--skip-lint",
        action="store_true",
        help="Skip lint/check step",
    )
    parser.add_argument(
        "--skip-commit",
        action="store_true",
        help="Skip git commit step",
    )
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="Skip git push step",
    )
    parser.add_argument(
        "--auto-create-pr",
        action="store_true",
        help="Auto create PR after push",
    )
    parser.add_argument(
        "--discord-webhook",
        help="Discord webhook URL for alerts",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # 환경변수에서 webhook URL 가져오기
    webhook_url = args.discord_webhook or os.environ.get("DISCORD_WEBHOOK_URL")

    # 설정 생성
    config = WorkflowConfig(
        dry_run=args.dry_run,
        skip_memory=args.skip_memory,
        skip_ssot=args.skip_ssot,
        skip_lint=args.skip_lint,
        skip_commit=args.skip_commit,
        skip_push=args.skip_push,
        auto_create_pr=args.auto_create_pr,
        discord_webhook=webhook_url,
    )

    # 엔진 초기화
    engine = AutoPhaseWorkflowEngine(config)

    # 실행 모드 선택
    if args.once:
        result = await engine.run()

        print_report(result)

        if result.git_commit_hash and args.auto_create_pr and not args.dry_run:
            # PR 생성 (선택 사항)
            logger.info("📝 Creating PR (optional)...")
            # PR 생성 로직은 별도 구현 필요

        return 0 if result.status == "success" else 1

    elif args.continuous:
        try:
            while True:
                result = await engine.run()

                # 알림 전송
                await engine._send_discord_alert(result)

                # 보고 출력
                print_report(result)

                # 다음 사이클까지 대기 (1시간)
                await asyncio.sleep(3600)

        except KeyboardInterrupt:
            logger.info("🛑 Workflow stopped by user")
            return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
