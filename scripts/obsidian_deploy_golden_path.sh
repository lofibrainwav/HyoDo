#!/bin/bash
# scripts/obsidian_deploy_golden_path.sh
# AFO Kingdom Obsidian Deployment Automation (Golden Path)
# 眞善美孝永 - Scripts & Templates 정합성 강제화

set -euo pipefail

echo "🏰 AFO Kingdom - Obsidian Deployment Golden Path starting..."

# 0) 경로 입력 받기
if [ -z "${1:-}" ]; then
    read -r -p "Obsidian Vault 경로 (예: /Users/.../docs): " VAULT
else
    VAULT="$1"
fi

# 1) 유효성 검사 (眞)
test -d "$VAULT" || { echo "❌ ERROR: Vault not found: $VAULT"; exit 1; }
test -d "docs/Scripts" || { echo "❌ ERROR: repo docs/Scripts 없음"; exit 1; }
test -d "docs/_templates" || { echo "❌ ERROR: repo docs/_templates 없음"; exit 1; }

echo "🛡️  Vault validated: $VAULT"

# 2) 백업 생성 (善)
BACKUP="${VAULT}_BACKUP_$(date +%Y%m%d_%H%M%S)"
echo "🧯 백업 생성 중: $BACKUP"
rsync -a --delete "$VAULT/" "$BACKUP/"

# 3) Vault 내 구조 최적화 (美)
mkdir -p "$VAULT/Scripts"
mkdir -p "$VAULT/Templates"
mkdir -p "$VAULT/_templates/scripts" # 과도기적 호환성 보장용

# 4) 자산 주입 및 통합 (眞)
echo "🚀 자산 주입 및 통합 중..."

# Repo의 Scripts -> Vault/Scripts
rsync -a "docs/Scripts/" "$VAULT/Scripts/"

# Repo의 _templates -> Vault/Templates
rsync -a "docs/_templates/" "$VAULT/Templates/"

# Repo의 _templates/scripts 내 특수 스크립트(post_template.js 등)도 Vault/Scripts로 통합
if [ -d "docs/_templates/scripts" ]; then
    rsync -a "docs/_templates/scripts/" "$VAULT/Scripts/"
fi

# 5) 과도기적 미러링 (孝) - 설정이 바뀌기 전에도 동작 보장
rsync -a "$VAULT/Scripts/" "$VAULT/_templates/scripts/"

# 6) Templater 설정 자동 패치 (永)
echo "📝 Templater 설정 패치 중..."

# 가능한 설정 파일 후보들
TPL_CANDIDATES=(
    "$VAULT/.obsidian/plugins/templater-obsidian/data.json"
    "$VAULT/.obsidian/templater.json"
)

for TPL in "${TPL_CANDIDATES[@]}"; do
    if [ -f "$TPL" ]; then
        echo "🔍 Found config to patch: $TPL"
        BK="${TPL}.bak.$(date +%Y%m%d_%H%M%S)"
        cp "$TPL" "$BK"

        python3 - "$TPL" <<'PY'
import sys
import json
from pathlib import Path

path = Path(sys.argv[1])
try:
    with open(path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    changed = False
    
    # User Scripts Folder Patch
    if config.get("user_scripts_folder") == "_templates/scripts":
        config["user_scripts_folder"] = "Scripts"
        changed = True
    
    # Templates Folder Patch
    if config.get("templates_folder") == "_templates":
        config["templates_folder"] = "Templates"
        changed = True

    # Folder Templates mapping update
    if "folder_templates" in config:
        for entry in config["folder_templates"]:
            if entry.get("template", "").startswith("_templates/"):
                entry["template"] = entry["template"].replace("_templates/", "Templates/")
                changed = True
    
    # templates_pairs update
    if "templates_pairs" in config:
        for pair in config["templates_pairs"]:
            if len(pair) > 1 and pair[1].startswith("_templates/"):
                pair[1] = pair[1].replace("_templates/", "Templates/")
                changed = True

    if changed:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ Config patched: {path}")
    else:
        print(f"ℹ️  Config already up to date: {path}")

except Exception as e:
    print(f"⚠️  Config patch error: {e}")
PY
    fi
done

echo "✅ Vault 패정 및 동기화 완료!"
echo "- Scripts: $VAULT/Scripts (total: $(find "$VAULT/Scripts" -maxdepth 1 -not -path "$VAULT/Scripts" | wc -l | xargs))"
echo "- Templates: $VAULT/Templates (total: $(find "$VAULT/Templates" -maxdepth 1 -not -path "$VAULT/Templates" | wc -l | xargs))"
echo "- Rollback: rsync -a --delete \"$BACKUP/\" \"$VAULT/\""
echo ""
echo "💡 마지막 단계: Obsidian 앱에서 'Community Plugins'를 통해 바이너리를 설치/업데이트 하세요."
