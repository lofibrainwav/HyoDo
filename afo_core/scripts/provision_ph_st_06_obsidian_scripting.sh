#!/bin/bash
set -euo pipefail

# PH-ST-06: Obsidian Scripting Orchestration — code provisioning
# This script provisions the scripting environment for Obsidian, enabling
# Templater scripts and automation logic.

if [ -d "packages/afo-core" ]; then
    ROOT="$(pwd)"
elif [ -d "../packages/afo-core" ]; then
    cd ..
    ROOT="$(pwd)"
else
    ROOT="$(git rev-parse --show-toplevel)"
fi

VAULT_REL="config/obsidian/vault"
VAULT="$ROOT/$VAULT_REL"

SCRIPTS_DIR="$VAULT/scripts"
TEMPLATES_DIR="$VAULT/templates"

echo "🧠 Provisioning Obsidian Scripting at: $VAULT"

mkdir -p "$SCRIPTS_DIR" "$TEMPLATES_DIR"

# 1. create_auto_moc.js (Logic to update MOCs automatically)
cat > "$SCRIPTS_DIR/create_auto_moc.js" <<'JS'
/**
 * Auto-MOC Updater
 * Scans the Vault for tags/folders and updates Map of Content files.
 * Intended to be run via Templater or QuickAdd.
 */
async function update_moc(tp) {
    const files = app.vault.getMarkdownFiles();
    let moc_content = "# Auto-Generated MOC\n\n";

    // Example: List all files in 'ph' folder
    const ph_files = files.filter(f => f.path.startsWith("ph/"));
    
    moc_content += "## Project Phases\n";
    ph_files.forEach(f => {
        moc_content += `- [[${f.basename}]]\n`;
    });

    return moc_content;
}
module.exports = update_moc;
JS

# 2. auto_moc_template.md (Templater file)
cat > "$TEMPLATES_DIR/Auto_MOC_Template.md" <<'MD'
<%*
const update_moc = require(app.vault.adapter.basePath + "/scripts/create_auto_moc.js");
tR += await update_moc(tp);
%>
MD

echo "✅ Created Script: $SCRIPTS_DIR/create_auto_moc.js"
echo "✅ Created Template: $TEMPLATES_DIR/Auto_MOC_Template.md"

echo "[ok] PH-ST-06 Obsidian Scripting provisioned."
