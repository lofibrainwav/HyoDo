"""
ACL Audit Logging Middleware - 모든 allow/deny 결정을 JSONL로 기록
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class ACLAuditMiddleware(BaseHTTPMiddleware):
    """ACL 결정 감사 로그 미들웨어"""

    def __init__(self, app, log_file: Path | None = None) -> None:
        super().__init__(app)
        if log_file is None:
            # 기본 로그 파일: ~/.afo/acl_audit.jsonl
            base_dir = Path.home() / ".afo"
            base_dir.mkdir(parents=True, exist_ok=True)
            log_file = base_dir / "acl_audit.jsonl"

        self.log_file = log_file
        self._rotate_if_needed()

    async def dispatch(self, request: Request, call_next):
        # Request ID 생성 (추적용)
        request_id = str(uuid.uuid4())[:12]
        request.state.request_id = request_id

        # ACL 결정 기록을 위한 컨텍스트
        request.state.acl_decision = None
        request.state.acl_key_info = None

        # 다음 미들웨어/라우터 실행
        response = await call_next(request)

        # ACL 결정이 있었다면 로그 기록
        if hasattr(request.state, "acl_decision") and request.state.acl_decision:
            await self._log_decision(request)

        return response

    async def _log_decision(self, request: Request):
        """ACL 결정 로그 기록"""
        decision_data = request.state.acl_decision
        key_info = getattr(request.state, "acl_key_info", None)

        # 클라이언트 IP 추출
        client_ip = self._get_client_ip(request)

        # 로그 엔트리 생성
        log_entry = {
            "ts": datetime.now().isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query) if request.url.query else "",
            "decision": decision_data["decision"],
            "reason": decision_data["reason"],
            "key_name": key_info.get("name") if key_info else None,
            "scopes": key_info.get("scopes", []) if key_info else [],
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", ""),
        }

        # JSONL 형식으로 기록
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            # 로그 실패는 시스템에 영향을 주지 않음
            print(f"⚠️ ACL audit log failed: {e}")

    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 추출"""
        # X-Forwarded-For 헤더 우선 (프록시 뒤에 있을 때)
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            # 첫 번째 IP 사용 (프록시 체인에서)
            return x_forwarded_for.split(",")[0].strip()

        # X-Real-IP 헤더
        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip

        # 기본 클라이언트 주소
        client_host = getattr(request.client, "host", None) if request.client else None
        return client_host or "unknown"

    def _rotate_if_needed(self) -> None:
        """로그 파일 크기 제한 및 로테이션"""
        max_size = 10 * 1024 * 1024  # 10MB

        try:
            if self.log_file.exists() and self.log_file.stat().st_size > max_size:
                # 현재 파일을 백업
                backup_file = self.log_file.with_suffix(
                    f".backup_{int(datetime.now().timestamp())}"
                )
                self.log_file.rename(backup_file)

                # 새 로그 파일 생성
                with open(self.log_file, "w") as f:
                    f.write(
                        f'{"ts": "{datetime.now().isoformat()}", "event": "log_rotated", "previous_file": "{backup_file.name}"}\n'
                    )

        except Exception as e:
            print(f"⚠️ ACL audit log rotation failed: {e}")

    def get_recent_logs(self, limit: int = 100) -> list[dict]:
        """최근 로그 조회 (관리용)"""
        logs = []
        try:
            with open(self.log_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
                        if len(logs) >= limit:
                            break
        except Exception as e:
            print(f"⚠️ Failed to read audit logs: {e}")

        return logs[::-1]  # 최신순으로 반환

    def get_stats(self) -> dict:
        """로그 통계 (관리용)"""
        stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "denied_requests": 0,
            "unique_keys": set(),
            "top_paths": {},
            "recent_denies": [],
        }

        try:
            with open(self.log_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        stats["total_requests"] += 1

                        if entry["decision"] == "ALLOW":
                            stats["allowed_requests"] += 1
                        elif entry["decision"] == "DENY":
                            stats["denied_requests"] += 1
                            stats["recent_denies"].append(entry)

                        if entry.get("key_name"):
                            stats["unique_keys"].add(entry["key_name"])

                        path = entry["path"]
                        stats["top_paths"][path] = stats["top_paths"].get(path, 0) + 1

            # 최근 deny만 유지
            stats["recent_denies"] = stats["recent_denies"][-10:]
            stats["unique_keys"] = len(stats["unique_keys"])

        except Exception as e:
            print(f"⚠️ Failed to generate audit stats: {e}")

        return stats


# 전역 감사 로그 미들웨어 인스턴스
audit_middleware = ACLAuditMiddleware(None)
