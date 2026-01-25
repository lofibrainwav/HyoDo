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
