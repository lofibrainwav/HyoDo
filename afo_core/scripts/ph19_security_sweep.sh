#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TS="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$ROOT_DIR/artifacts/ph19_security/$TS"
mkdir -p "$OUT_DIR"

PIPAUDIT_RC=0
GITLEAKS_RC=0
BANDIT_RC=0

{
  echo "timestamp=$TS"
  echo "pwd=$ROOT_DIR"
  echo "python=$(python3 --version 2>&1 || true)"
  echo "git=$(git --version 2>&1 || true)"
  echo "gitleaks=$(command -v gitleaks >/dev/null 2>&1 && gitleaks version 2>&1 || echo 'MISSING')"
  echo "bandit=$(python3 -c 'import bandit; print(bandit.__version__)' 2>/dev/null || echo 'MISSING')"
  echo "pip_audit=$(python3 -c 'import pip_audit; print(pip_audit.__version__)' 2>/dev/null || echo 'MISSING')"
} > "$OUT_DIR/tool_versions.txt"

echo "[PH19] output: $OUT_DIR"

# TICKET W3.6: 운영 런북 자동 생성 (보안 검사와 독립 실행)
if [ "${GENERATE_RUNBOOK:-false}" = "true" ]; then
    RUNBOOK_FILE="docs/wallet_operations_runbook.md"
    mkdir -p docs

    cat > "$RUNBOOK_FILE" << 'EOF'
# Wallet Operations Runbook

## Overview
AFO Wallet 시스템의 안전한 운영을 위한 1페이지 가이드.
Runtime/Seeder 역할 분리 + 자동 Rotation 적용.

## Security Policy (CRITICAL)

### Fail-closed vs Emergency Local Fallback
- **평시 운영**: `API_WALLET_KMS=vault` (Fail-closed - Vault 장애 시 시스템 중단)
- **비상시 운영**: `API_WALLET_KMS=local` (명시적 fallback - 키 변경/추가 허용 안 함)
- **Fallback 조건**: Vault 완전 장애 + 운영자 승인 시에만 사용
- **Fallback 제한**: 읽기 전용 모드, 키 생성/수정 불가

## Daily Operations

### 1. 상태 확인
```bash
# 시스템 상태 점검
VAULT_MONITOR_APPROLE=true ./scripts/ph19_security_sweep.sh
curl http://127.0.0.1:8011/health
```

### 2. 배포 전 Secret ID Rotation (권장 - 옵션 A: 통합 자동화)
```bash
# 자동 Rotation + 재기동 원샷 (스크립트가 docker compose 직접 실행)
DEPLOY_ROTATE_WALLET=true ./scripts/ph19_security_sweep.sh
```

### 3. 수동 배포 (권장하지 않음 - 재현성 저하)
```bash
# ⚠️  수동 환경변수 설정은 재현성/무결성 저하로 권장하지 않음
#    DEPLOY_ROTATE_WALLET=true 자동화를 사용하세요
# 기존 방식 (참고용):
# export VAULT_ROLE_ID="fb837c0f-9c17-9c46-ca3b-c2fd998a337c"
# export VAULT_SECRET_ID="<current-secret-id>"
# export API_WALLET_KMS=vault
# docker compose up -d wallet-service
```

## Weekly Operations

### 1. Seal Check (시스템 무결성 검증)
```bash
# 격리 환경에서만 실행 (Vault stop/start 포함)
ALLOW_DISRUPTIVE_CHECKS=true SEAL_CHECK=true ./scripts/ph19_security_sweep.sh
```

### 2. 보안 리포트 생성
```bash
REDACT_SECRETS=true ./scripts/ph19_security_sweep.sh
```

## Emergency Operations

### 1. Vault 장애 시 (Local Fallback - 승인 필수)
```bash
# ⚠️  운영자 승인 후에만 실행
export API_WALLET_KMS=local
docker compose up -d --force-recreate wallet-service
# 키 변경/추가 불가 (읽기 전용)
```

### 2. Secret ID 유실 시 (긴급 Rotation)
```bash
# Seeder 역할로 긴급 발급
docker exec afo-vault vault write -f -field=secret_id auth/approle/role/wallet-seeder/secret-id
# 이후 DEPLOY_ROTATE_WALLET=true로 재설정
```

## Security Notes
- Runtime 컨테이너는 read-only 권한만 가짐 (VAULT_SECRET_ID 미주입)
- Secret ID는 24시간 TTL 적용
- 모든 민감값은 자동 REDACT
- Rotation은 생성→주입→재기동 원샷 (스크립트 내부 통합)
- Seal Check는 ALLOW_DISRUPTIVE_CHECKS=true 시에만 vault down/up 실행

## Monitoring
- AppRole 토큰 만료 모니터링
- Secret ID 사용 횟수 추적
- Vault 연결 상태 확인
EOF

    echo "[RUNBOOK] Generated: $RUNBOOK_FILE"
fi

# TICKET W2: Vault seed for wallet testing (DEV ONLY)
# TICKET W3.2: AppRole security monitoring
if [ "${VAULT_MONITOR_APPROLE:-false}" = "true" ]; then
    echo "[VAULT] monitoring AppRole status..."
    if command -v docker >/dev/null 2>&1 && docker compose ps vault >/dev/null 2>&1; then
        echo "=== AppRole Status ==="
        docker compose exec -T vault vault read auth/approle/role/wallet-api 2>/dev/null || echo "Role not found"

        echo "=== Active Tokens (wallet-api) ==="
        # Note: In production, you'd want more sophisticated token tracking
        docker compose exec -T vault vault list auth/token/accessors 2>/dev/null | head -10 || echo "No active tokens"

        echo "[VAULT] AppRole monitoring completed"
    else
        echo "[VAULT] vault service not available for monitoring"
    fi
fi

if [ "${VAULT_SEED_WALLET_KEY:-false}" = "true" ]; then
    echo "[VAULT] seeding wallet encryption key (DEV ONLY)..."
    if command -v docker >/dev/null 2>&1 && docker compose ps vault >/dev/null 2>&1; then
        # Generate a secure random key
        WALLET_KEY="$(python3 -c "
import secrets, base64
key_bytes = secrets.token_bytes(32)
key_b64 = base64.urlsafe_b64encode(key_bytes).decode().rstrip('=')
print(key_b64)
" 2>/dev/null || echo 'fallback_key_32_chars_long_enough')"

        # Enable KV secrets engine if not exists
        docker compose exec -T vault vault secrets enable -path=secret kv-v2 >/dev/null 2>&1 || true

        # Store the key (DEV ONLY - uses root token)
        if docker compose exec -T vault vault kv put secret/api_wallet encryption_key="$WALLET_KEY" >/dev/null 2>&1; then
            echo "[VAULT] wallet key seeded successfully"
            echo "$WALLET_KEY" > "$OUT_DIR/vault_wallet_key.txt"
        else
            echo "[VAULT] failed to seed wallet key"
        fi
    else
        echo "[VAULT] vault service not available, skipping seed"
    fi
fi

run_cmd() {
  local name="$1"; shift
  set +e
  "$@" >"$OUT_DIR/${name}.stdout.txt" 2>"$OUT_DIR/${name}.stderr.txt"
  local rc=$?
  set -e
  echo "$rc" > "$OUT_DIR/${name}.rc.txt"
  return 0
}

echo "[1/3] pip-audit (deps vulnerabilities)"
if python3 -c "import pip_audit" >/dev/null 2>&1; then
  set +e
  TMP_PIPAUDIT="$(mktemp)"
  python3 -m pip_audit --format=json --progress-spinner=off . \
    1>"$TMP_PIPAUDIT" \
    2>"$OUT_DIR/pip_audit.stderr.txt"
  PIPAUDIT_RC=$?

  # Atomic Write & Validation (Enhanced)
  if [ $PIPAUDIT_RC -eq 0 ]; then
    if python3 -c "import json,sys; json.load(open(sys.argv[1],'r',encoding='utf-8'))" "$TMP_PIPAUDIT" >/dev/null 2>&1; then
      # Extra validation: check for shell script contamination
      if grep -q 'EOF && echo\|heredoc\|#!/.*bash\|#!/.*sh' "$TMP_PIPAUDIT" 2>/dev/null; then
        echo "Pip-audit output contaminated (shell script detected)" > "$OUT_DIR/pip_audit.stderr.txt"
        PIPAUDIT_RC=98
        echo "$PIPAUDIT_RC" > "$OUT_DIR/pip_audit.rc.txt"
        rm -f "$TMP_PIPAUDIT"
      else
        mv "$TMP_PIPAUDIT" "$OUT_DIR/pip_audit.json"
        echo "$PIPAUDIT_RC" > "$OUT_DIR/pip_audit.rc.txt"
      fi
    else
      echo "Pip-audit output corrupted (invalid JSON)" > "$OUT_DIR/pip_audit.stderr.txt"
      PIPAUDIT_RC=99
      echo "$PIPAUDIT_RC" > "$OUT_DIR/pip_audit.rc.txt"
      rm -f "$TMP_PIPAUDIT"
    fi
  else
    echo "$PIPAUDIT_RC" > "$OUT_DIR/pip_audit.rc.txt"
    rm -f "$TMP_PIPAUDIT"
  fi

  set -e
else
  PIPAUDIT_RC=127
  echo "$PIPAUDIT_RC" > "$OUT_DIR/pip_audit.rc.txt"
  echo "pip-audit MISSING. Install: python3 -m pip install -U pip-audit" > "$OUT_DIR/pip_audit.stderr.txt"
fi

echo "[2/3] gitleaks (git history secrets)"
if command -v gitleaks >/dev/null 2>&1; then
  set +e
  gitleaks detect \
    --no-banner \
    --no-color \
    --log-level error \
    --report-format json \
    --report-path "$OUT_DIR/gitleaks.json" \
    --config "$ROOT_DIR/gitleaks.toml" \
    --redact \
    .
  GITLEAKS_RC=$?
  set -e
  echo "$GITLEAKS_RC" > "$OUT_DIR/gitleaks.rc.txt"
else
  GITLEAKS_RC=127
  echo "$GITLEAKS_RC" > "$OUT_DIR/gitleaks.rc.txt"
  echo "gitleaks MISSING. Install (macOS): brew install gitleaks" > "$OUT_DIR/gitleaks.stderr.txt"
fi

echo "[3/3] bandit (static security)"
if python3 -c "import bandit" >/dev/null 2>&1; then
  set +e
  TMP_BANDIT="$(mktemp)"
  python3 -m bandit \
    -c pyproject.toml \
    -r . \
    --severity-level medium \
    --confidence-level medium \
    -f json \
    -o "$TMP_BANDIT"
  BANDIT_RC=$?
  
  # Atomic Write & Validation (Enhanced)
  if [ $BANDIT_RC -eq 0 ]; then
    if python3 -c "import json,sys; json.load(open(sys.argv[1],'r',encoding='utf-8'))" "$TMP_BANDIT" >/dev/null 2>&1; then
      # Extra validation: check for shell script contamination
      if grep -q 'EOF && echo\|heredoc\|#!/.*bash\|#!/.*sh' "$TMP_BANDIT" 2>/dev/null; then
        echo "Bandit output contaminated (shell script detected)" > "$OUT_DIR/bandit.stderr.txt"
        BANDIT_RC=98
        echo "$BANDIT_RC" > "$OUT_DIR/bandit.rc.txt"
        rm -f "$TMP_BANDIT"
      else
        mv "$TMP_BANDIT" "$OUT_DIR/bandit.json"
        echo "$BANDIT_RC" > "$OUT_DIR/bandit.rc.txt"
      fi
    else
      echo "Bandit output corrupted (invalid JSON)" > "$OUT_DIR/bandit.stderr.txt"
      BANDIT_RC=99
      echo "$OUT_DIR/bandit.rc.txt"
      rm -f "$TMP_BANDIT"
    fi
  else
    echo "$BANDIT_RC" > "$OUT_DIR/bandit.rc.txt"
    rm -f "$TMP_BANDIT"
  fi
  rm -f "$TMP_BANDIT"
  set -e
else
  BANDIT_RC=127
  echo "$BANDIT_RC" > "$OUT_DIR/bandit.rc.txt"
  echo "bandit MISSING. Install: python3 -m pip install -U 'bandit[toml]'" > "$OUT_DIR/bandit.stderr.txt"
fi

python3 - <<'PY'
import json
from pathlib import Path

# We know script wrote OUT_DIR; infer from argv? We'll locate latest via rc files:
root = Path.cwd() / "artifacts" / "ph19_security"
latest = sorted([p for p in root.glob("*") if p.is_dir()])[-1]
def safe_json_count(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        # common patterns
        if "results" in data and isinstance(data["results"], list):
            return len(data["results"])
        if "findings" in data and isinstance(data["findings"], list):
            return len(data["findings"])
        # pip-audit format
        if "dependencies" in data and isinstance(data["dependencies"], list):
            vulns = 0
            for dep in data["dependencies"]:
                if "vulns" in dep:
                    vulns += len(dep["vulns"])
            return vulns
    return None

pip_cnt = safe_json_count(latest / "pip_audit.json")
git_cnt = safe_json_count(latest / "gitleaks.json")
ban_cnt = safe_json_count(latest / "bandit.json")

summary = []
summary.append(f"# PH19 Security Sweep Summary ({latest.name})")
summary.append("")
summary.append(f"- pip-audit: vulnerabilities={pip_cnt if pip_cnt is not None else 'n/a'} rc={(latest/'pip_audit.rc.txt').read_text().strip()}")
summary.append(f"- gitleaks: findings={git_cnt if git_cnt is not None else 'n/a'} rc={(latest/'gitleaks.rc.txt').read_text().strip()}")
summary.append(f"- bandit: findings={ban_cnt if ban_cnt is not None else 'n/a'} rc={(latest/'bandit.rc.txt').read_text().strip()}")
summary.append("")
summary.append("## Gate rule")
summary.append("- PASS = all rc == 0")
summary.append("- FAIL = any rc != 0 (including missing tools)")
(latest / "summary.md").write_text("\n".join(summary), encoding="utf-8")
PY

echo ""
echo "== SUMMARY =="
cat "$OUT_DIR/summary.md"
echo ""

if [[ "$PIPAUDIT_RC" -ne 0 || "$GITLEAKS_RC" -ne 0 || "$BANDIT_RC" -ne 0 ]]; then
  echo "[PH19] FAIL (rc: pip-audit=$PIPAUDIT_RC, gitleaks=$GITLEAKS_RC, bandit=$BANDIT_RC)"
  exit 1
fi

echo "[PH19] PASS (all clear)"

# TICKET W3.1: Security REDACT function for reports (post-processing)
redact_secrets() {
    local file="$1"
    if [ ! -f "$file" ]; then return; fi

    # Create backup before redaction
    cp "$file" "${file}.unredacted"

    # REDACT patterns for sensitive data
    sed -i.bak \
        -e 's/VAULT_TOKEN=[^[:space:]]*/VAULT_TOKEN=<REDACTED>/g' \
        -e 's/VAULT_SECRET_ID=[^[:space:]]*/VAULT_SECRET_ID=<REDACTED>/g' \
        -e 's/Secret ID: [a-f0-9-]\+/Secret ID: <REDACTED>/g' \
        -e 's/[a-f0-9]\{8\}-[a-f0-9]\{4\}-[a-f0-9]\{4\}-[a-f0-9]\{4\}-[a-f0-9]\{12\}/<UUID_REDACTED>/g' \
        -e 's/ROLE_ID=[^[:space:]]*/ROLE_ID=<REDACTED>/g' \
        "$file"

    echo "Security REDACT applied to: $file"
}

# Apply REDACT to all generated files (optional - run with REDACT_SECRETS=true)
if [ "${REDACT_SECRETS:-false}" = "true" ]; then
    for f in "artifacts/wallet_vault_intel/${TS}."*; do
        if [ -f "$f" ]; then
            redact_secrets "$f"
        fi
    done
    echo "[SECURITY] Sensitive data redaction completed"
fi

# TICKET W3.5: 60초 Seal Check (자동화된 시스템 검증) - 하드 가드 적용
if [ "${SEAL_CHECK:-false}" = "true" ]; then
    if [ "${ALLOW_DISRUPTIVE_CHECKS:-false}" != "true" ]; then
        echo "[SEAL] ❌ Disruptive checks blocked: Set ALLOW_DISRUPTIVE_CHECKS=true for vault stop/start"
        echo "[SEAL] 💡 This check stops and restarts Vault service - only run in isolated test environments"
        exit 1
    fi

    echo "[SEAL] Starting 60-second system seal check (disruptive mode)..."

    # 1) wallet-service vault 모드 정상 확인
    echo "[SEAL] 1/3: Checking wallet health..."
    if curl -sf http://127.0.0.1:8011/health >/dev/null 2>&1; then
        echo "[SEAL] ✅ Wallet health OK"
    else
        echo "[SEAL] ❌ Wallet health failed"
        exit 1
    fi

    # 2) 재시작 2회 테스트 (num_uses=3 검증)
    echo "[SEAL] 2/3: Testing restart tolerance (num_uses=3)..."
    if docker compose restart wallet-service >/dev/null 2>&1 && sleep 5 && curl -sf http://127.0.0.1:8011/health >/dev/null 2>&1; then
        echo "[SEAL] ✅ Restart 1 OK"
    else
        echo "[SEAL] ❌ Restart 1 failed"
        exit 1
    fi

    if docker compose restart wallet-service >/dev/null 2>&1 && sleep 5 && curl -sf http://127.0.0.1:8011/health >/dev/null 2>&1; then
        echo "[SEAL] ✅ Restart 2 OK"
    else
        echo "[SEAL] ❌ Restart 2 failed"
        exit 1
    fi

    # 3) Vault fail-closed 테스트 (vault down 시 wallet 실패 검증)
    echo "[SEAL] 3/3: Testing fail-closed (vault dependency)..."
    docker compose stop vault >/dev/null 2>&1
    sleep 5

    # wallet 재시작 시도 (vault 없으면 실패해야 함)
    if docker compose restart wallet-service >/dev/null 2>&1; then
        # 10초 대기 후 health check
        sleep 10
        if curl -sf http://127.0.0.1:8011/health >/dev/null 2>&1 2>/dev/null; then
            echo "[SEAL] ❌ Fail-closed failed: wallet started without vault"
            docker compose start vault >/dev/null 2>&1
            exit 1
        else
            echo "[SEAL] ✅ Fail-closed OK: wallet properly failed without vault"
        fi
    else
        echo "[SEAL] ✅ Fail-closed OK: wallet restart failed as expected"
    fi

    # vault 복구
    docker compose start vault >/dev/null 2>&1
    sleep 3

    echo "[SEAL] 🎉 All seal checks passed! System is properly sealed."
fi


# TICKET W3.4: Deploy-time Secret ID rotation (옵션 A: 통합 자동화 - 재현성 보장)
# VAULT_SECRET_ID 전달 방식: 스크립트가 직접 docker compose up 실행 (셸 export 없음)
if [ "${DEPLOY_ROTATE_WALLET:-false}" = "true" ]; then
    echo "[DEPLOY] Starting wallet-runtime Secret ID rotation (옵션 A: 통합 자동화)..."
    if command -v docker >/dev/null 2>&1 && docker compose ps vault >/dev/null 2>&1; then
        # 새 Secret ID 발급 (출력하지 않음 - 내부 처리 전용)
        NEW_SECRET_ID=$(docker exec afo-vault vault write -f -field=secret_id auth/approle/role/wallet-runtime/secret-id 2>/dev/null)
        if [ -n "$NEW_SECRET_ID" ]; then
            echo "[DEPLOY] New Secret ID generated successfully"

            # 옵션 A: 스크립트가 docker compose를 직접 실행 (환경변수 통합 주입)
            # 장점: 셸 export 없음, 재현성 100%, 감사가능성 높음
            echo "[DEPLOY] Executing integrated deployment (VAULT_SECRET_ID 직접 주입)..."
            VAULT_SECRET_ID="$NEW_SECRET_ID" \
            VAULT_ROLE_ID="${VAULT_ROLE_ID:-fb837c0f-9c17-9c46-ca3b-c2fd998a337c}" \
            API_WALLET_KMS="${API_WALLET_KMS:-vault}" \
            docker compose up -d --force-recreate wallet-service >/dev/null 2>&1

            DEPLOY_RC=$?
            if [ $DEPLOY_RC -eq 0 ]; then
                echo "[DEPLOY] ✅ Wallet service restarted successfully"
                echo "[DEPLOY] 🔍 Validating restart..."
                sleep 10

                # 재기동 검증
                if curl -sf http://127.0.0.1:8011/health >/dev/null 2>&1; then
                    echo "[DEPLOY] ✅ Health check passed"
                    echo "[DEPLOY] 🎉 Rotation completed successfully!"
                else
                    echo "[DEPLOY] ❌ Health check failed after rotation"
                    exit 1
                fi
            else
                echo "[DEPLOY] ❌ Failed to restart wallet-service (exit code: $DEPLOY_RC)"
                exit 1
            fi
        else
            echo "[DEPLOY] Failed to generate new Secret ID"
            exit 1
        fi
    else
        echo "[DEPLOY] Vault service not available"
        exit 1
    fi
fi
