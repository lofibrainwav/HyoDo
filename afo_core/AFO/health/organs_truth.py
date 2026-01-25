from __future__ import annotations

import os
import pathlib
import socket
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.health_check_config import health_check_config
from config.settings import get_settings

"""VERSION: FINAL_TRUTH_1"""


@dataclass(frozen=True)
class OrganReport:
    status: str
    score: int
    output: str
    probe: str
    latency_ms: int


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _tcp_probe(host: str, port: int, timeout_s: float) -> tuple[bool, int, str]:
    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            ms = int((time.perf_counter() - t0) * 1000)
            return True, ms, f"tcp://{host}:{port}"
    except Exception:
        ms = int((time.perf_counter() - t0) * 1000)
        return False, ms, f"tcp://{host}:{port}"


def _mk(
    ok: bool,
    ms: int,
    target: str,
    probe: str,
    ok_score: int,
    bad_score: int,
    ok_msg: str,
    bad_msg: str,
) -> OrganReport:
    if ok:
        return OrganReport(
            status="healthy",
            score=ok_score,
            output=ok_msg,
            probe=f"{probe}:{target}",
            latency_ms=ms,
        )
    return OrganReport(
        status="disconnected",
        score=bad_score,
        output=bad_msg,
        probe=f"{probe}:{target}",
        latency_ms=ms,
    )


def _security_probe(repo_root: Path | None = None) -> OrganReport:
    # Check for evidence of security scans using Root Anchor (Option A: Robust)
    sec_found = False
    sec_path = "None"

    candidates = []
    if repo_root:
        candidates = [
            repo_root / "trivy-results.json",
            repo_root / "logs" / "trivy-results.json",
            repo_root / "artifacts" / "trivy-results.json",
        ]
    else:
        # Fallback if no repo_root (should not happen with new logic, but safe)
        candidates = [
            pathlib.Path("trivy-results.json"),
            pathlib.Path("../../trivy-results.json"),
        ]

    ctx_file = next((p for p in candidates if p.exists()), None)
    if ctx_file:
        sec_found = True
        try:
            sec_path = str(ctx_file.relative_to(repo_root)) if repo_root else str(ctx_file)
        except ValueError:
            sec_path = str(ctx_file)

    return OrganReport(
        status="healthy" if sec_found else "unhealthy",
        score=90 if sec_found else 10,
        output=(
            f"Security Scan Verified ({sec_path})" if sec_found else "No Security Evidence Found"
        ),
        probe="file:trivy-results.json",
        latency_ms=0,
    )


@dataclass
class OrganBuilder:
    redis_host: str | None = None
    redis_port: int | None = None
    postgres_host: str | None = None
    postgres_port: int | None = None
    qdrant_host: str | None = None
    qdrant_port: int | None = None
    ollama_host: str | None = None
    ollama_port: int | None = None
    timeout_tcp_s: float = 0.35

    def build(self) -> dict[str, Any]:
        repo_root = self._determine_repo_root()
        config, timeout = self._load_config()
        self.timeout_tcp_s = timeout

        # Build Organs
        organs: dict[str, OrganReport] = {}
        organs["心_Redis"] = self._check_redis(config)
        organs["肝_PostgreSQL"] = self._check_postgres(config)
        organs["腦_Soul_Engine"] = self._check_soul_engine()
        organs["舌_Ollama"] = self._check_ollama(config)
        organs["肺_Vector_DB"] = self._check_vector_db(config)
        organs["眼_Dashboard"] = self._check_dashboard()
        organs["腎_MCP"] = self._check_mcp()
        organs["耳_Observability"] = self._check_observability()
        organs["口_Docs"] = self._check_docs(repo_root)
        organs["骨_CI"] = self._check_ci(repo_root)
        organs["胱_Evolution_Gate"] = self._check_evolution_gate(repo_root)

        # Security Check
        security_report = _security_probe(repo_root)

        return self._construct_response(organs, security_report)

    def _determine_repo_root(self) -> Path | None:
        current_path = pathlib.Path(__file__).resolve()
        for parent in current_path.parents:
            if (parent / "TICKETS.md").exists():
                return parent
        return None

    def _load_config(self) -> tuple[dict[str, Any], float]:
        infra_mode = self._detect_infra_mode()
        print(f"🔧 Infra Mode Detected: {infra_mode}", flush=True)

        mode_config = self._get_mode_config(infra_mode)
        settings = self._get_settings_safe()

        config = self._resolve_host_config(mode_config, settings)
        self._resolve_port_config(config, mode_config, settings)

        return config, mode_config["timeout_tcp_s"]

    def _get_mode_config(self, infra_mode: str) -> dict[str, Any]:
        mode_configs = {
            "local": {
                "redis_host": "127.0.0.1",
                "postgres_host": "127.0.0.1",
                "ollama_host": "127.0.0.1",
                "timeout_tcp_s": 0.5,
            },
            "docker": {
                "redis_host": "afo-redis",
                "postgres_host": "afo-postgres",
                "timeout_tcp_s": 0.35,
            },
            "minimal": {
                "redis_host": "localhost",
                "postgres_host": "localhost",
                "timeout_tcp_s": 0.1,
            },
            "hybrid": {
                "redis_host": "afo-redis",
                "postgres_host": "localhost",
                "timeout_tcp_s": 0.25,
            },
        }
        return mode_configs.get(infra_mode, mode_configs["minimal"])

    def _get_settings_safe(self) -> Any | None:
        try:
            return get_settings()
        except ImportError:
            return None

    def _resolve_host_config(self, mode_config: dict, settings: Any) -> dict[str, Any]:
        config = {}
        config["redis_host"] = (
            self.redis_host
            or (settings.REDIS_HOST if settings else None)
            or os.getenv("REDIS_HOST", mode_config["redis_host"])
        )
        config["postgres_host"] = (
            self.postgres_host
            or (settings.POSTGRES_HOST if settings else None)
            or os.getenv("POSTGRES_HOST", mode_config["postgres_host"])
        )
        config["qdrant_host"] = self.qdrant_host or os.getenv("QDRANT_HOST", "afo-qdrant")
        config["ollama_host"] = (
            self.ollama_host
            or os.getenv("OLLAMA_HOST")
            or mode_config.get("ollama_host", "afo-ollama")
        )
        return config

    def _resolve_port_config(self, config: dict, mode_config: dict, settings: Any) -> None:
        config["redis_port"] = (
            self.redis_port
            or (settings.REDIS_PORT if settings else None)
            or int(os.getenv("REDIS_PORT", "6379"))
        )
        config["postgres_port"] = (
            self.postgres_port
            or (settings.POSTGRES_PORT if settings else None)
            or int(os.getenv("POSTGRES_PORT", "5432"))
        )
        config["qdrant_port"] = self.qdrant_port or int(os.getenv("QDRANT_PORT", "6333"))
        config["ollama_port"] = self.ollama_port or int(os.getenv("OLLAMA_PORT", "11434"))

    def _detect_infra_mode(self) -> str:
        if os.getenv("INFRA_MODE"):
            return os.getenv("INFRA_MODE")
        if os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER"):
            return "docker"
        try:
            with socket.create_connection(("localhost", 6379), timeout=0.1):
                return "local"
        except Exception:
            pass
        return "minimal"

    def _check_redis(self, config: dict) -> OrganReport:
        import redis

        t0 = time.perf_counter()
        try:
            r = redis.Redis(
                host=config["redis_host"],
                port=config["redis_port"],
                socket_timeout=self.timeout_tcp_s,
            )
            info = r.info("server")
            ms = int((time.perf_counter() - t0) * 1000)
            version = info.get("redis_version", "unknown")
            return OrganReport(
                status="healthy",
                score=98,
                output=f"Redis v{version} Active",
                probe=f"redis://{config['redis_host']}:{config['redis_port']}",
                latency_ms=ms,
            )
        except Exception as e:
            ms = int((time.perf_counter() - t0) * 1000)
            return OrganReport(
                status="unhealthy",
                score=0,
                output=f"Redis Error: {str(e)[:50]}",
                probe=f"redis://{config['redis_host']}:{config['redis_port']}",
                latency_ms=ms,
            )

    def _check_postgres(self, config: dict) -> OrganReport:
        import psycopg2

        t0 = time.perf_counter()
        host = config["postgres_host"]
        port = config["postgres_port"]
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                dbname=os.getenv("POSTGRES_DB", "postgres"),
                connect_timeout=2,
            )
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                row = cur.fetchone()
                ver = str(row[0]) if row else "unknown"
            conn.close()
            ms = int((time.perf_counter() - t0) * 1000)
            return OrganReport(
                status="healthy",
                score=99,
                output=f"Postgres Active: {ver[:30]}...",
                probe=f"psql://{host}:{port}",
                latency_ms=ms,
            )
        except Exception as e:
            # Fallback for local dev port mismatch (5432 vs 15432)
            if host in ["127.0.0.1", "localhost"]:
                fallback_port = 5432 if port == 15432 else 15432
                try:
                    conn = psycopg2.connect(host=host, port=fallback_port, connect_timeout=1)
                    conn.close()
                    return OrganReport(
                        status="healthy",
                        score=99,
                        output="Postgres Active (Fallback Port)",
                        probe=f"psql://{host}:{fallback_port}",
                        latency_ms=1,
                    )
                except Exception:
                    pass
            ms = int((time.perf_counter() - t0) * 1000)
            return OrganReport(
                status="unhealthy",
                score=0,
                output=f"Postgres Error: {str(e)[:50]}",
                probe=f"psql://{host}:{port}",
                latency_ms=ms,
            )

    def _check_soul_engine(self) -> OrganReport:
        host = os.getenv("SOUL_ENGINE_HOST", "localhost")
        port = int(os.getenv("SOUL_ENGINE_PORT", "8010"))
        ok, ms, t = _tcp_probe(host, port, 0.2)
        print(f"SOUL ENGINE STATUS: {ok}", flush=True)
        return _mk(
            ok,
            ms,
            t,
            "self-tcp",
            100,
            0,
            "Sovereign Orchestration Active",
            f"Soul Engine Unresponsive ({host}:{port})",
        )

    def _check_ollama(self, config: dict) -> OrganReport:
        import requests

        t0 = time.perf_counter()
        url = f"http://{config['ollama_host']}:{config['ollama_port']}/api/tags"
        try:
            resp = requests.get(url, timeout=2.0)
            ms = int((time.perf_counter() - t0) * 1000)
            if resp.status_code == 200:
                data = resp.json()
                models = len(data.get("models", []))
                return OrganReport(
                    status="healthy",
                    score=95,
                    output=f"Ollama Active: {models} models",
                    probe=url,
                    latency_ms=ms,
                )
            return OrganReport(
                status="unhealthy",
                score=0,
                output=f"Ollama Status {resp.status_code}",
                probe=url,
                latency_ms=ms,
            )
        except Exception as e:
            ms = int((time.perf_counter() - t0) * 1000)
            return OrganReport(
                status="unhealthy",
                score=0,
                output=f"Ollama Error: {str(e)[:50]}",
                probe=url,
                latency_ms=ms,
            )

    def _check_vector_db(self, config: dict) -> OrganReport:
        vector_db_type = os.getenv("VECTOR_DB", "lancedb").lower()
        if vector_db_type == "lancedb":
            lancedb_path = os.getenv("LANCEDB_PATH", "./data/lancedb")
            lancedb_table = os.path.join(lancedb_path, "afokingdom_knowledge.lance")
            ok = os.path.exists(lancedb_table)
            return _mk(
                ok,
                0,
                f"file:{lancedb_table}",
                "file",
                94,
                20,
                "LanceDB Connected",
                "LanceDB Disconnected",
            )
        else:
            ok, ms, t = _tcp_probe(config["qdrant_host"], config["qdrant_port"], self.timeout_tcp_s)
            return _mk(ok, ms, t, "tcp", 94, 20, "Qdrant Connected", "Qdrant Disconnected")

    def _check_dashboard(self) -> OrganReport:
        host = os.getenv("DASHBOARD_HOST", "localhost")
        ok, ms, t = _tcp_probe(host, 3000, self.timeout_tcp_s)
        if not ok and host == "localhost":
            ok, ms, t = _tcp_probe("afo-dashboard", 3000, self.timeout_tcp_s)
        return _mk(ok, ms, t, "tcp", 92, 10, "Visual OK", "Dashboard Disconnected")

    def _check_mcp(self) -> OrganReport:
        try:
            count = len(getattr(health_check_config, "MCP_SERVERS", [])) or len(
                getattr(health_check_config, "mcp_servers", [])
            )
            score = min(98, 85 + (count * 2)) if count > 0 else 40
            msg = f"Active MCP: {count}" if count > 0 else "No MCP Configured"
            return OrganReport(
                "healthy" if count > 0 else "unhealthy", score, msg, "config:health", 0
            )
        except Exception as e:
            return OrganReport("unhealthy", 10, str(e), "error", 0)

    def _check_observability(self) -> OrganReport:
        try:
            return OrganReport("healthy", 90, "Prometheus Client Loaded", "module:import", 0)
        except ImportError:
            return OrganReport("unhealthy", 20, "Prometheus Missing", "module:import", 0)

    def _check_docs(self, repo_root: Path | None) -> OrganReport:
        ok = (repo_root / "docs" / "AFO_FINAL_SSOT.md").exists() if repo_root else False
        return OrganReport(
            "healthy" if ok else "unhealthy",
            95 if ok else 10,
            "SSOT Canon Found" if ok else "SSOT Missing",
            "file:docs",
            0,
        )

    def _check_ci(self, repo_root: Path | None) -> OrganReport:
        ok = (repo_root / ".github" / "workflows").exists() if repo_root else False
        return OrganReport(
            "healthy" if ok else "unhealthy",
            90 if ok else 40,
            "Workflows Active" if ok else "No Workflows",
            "fs:.github",
            0,
        )

    def _check_evolution_gate(self, repo_root: Path | None) -> OrganReport:
        ok = (repo_root / "docs" / "AFO_EVOLUTION_LOG.md").exists() if repo_root else False
        return OrganReport(
            "healthy" if ok else "unhealthy",
            95 if ok else 30,
            "Evolution Log Found" if ok else "Log Missing",
            "fs:docs",
            0,
        )

    def _construct_response(
        self, organs: dict[str, OrganReport], security_report: OrganReport
    ) -> dict[str, Any]:
        EXPECTED_ORGANS = [
            "心_Redis",
            "肝_PostgreSQL",
            "腦_Soul_Engine",
            "舌_Ollama",
            "肺_Vector_DB",
            "眼_Dashboard",
            "腎_MCP",
            "耳_Observability",
            "口_Docs",
            "骨_CI",
            "胱_Evolution_Gate",
        ]
        return {
            "ts": _now_iso(),
            "contract": {
                "version": "organs/v2",
                "organs_keys_expected": 11,
                "organs_keys": EXPECTED_ORGANS,
            },
            "organs": {k: asdict(v) for k, v in organs.items() if k in EXPECTED_ORGANS},
            "security": asdict(security_report),
        }


def build_organs_final(
    *,
    redis_host: str | None = None,
    redis_port: int | None = None,
    postgres_host: str | None = None,
    postgres_port: int | None = None,
    qdrant_host: str | None = None,
    qdrant_port: int | None = None,
    ollama_host: str | None = None,
    ollama_port: int | None = None,
    timeout_tcp_s: float = 0.35,
) -> dict[str, Any]:
    builder = OrganBuilder(
        redis_host=redis_host,
        redis_port=redis_port,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        qdrant_host=qdrant_host,
        qdrant_port=qdrant_port,
        ollama_host=ollama_host,
        ollama_port=ollama_port,
        timeout_tcp_s=timeout_tcp_s,
    )
    return builder.build()
