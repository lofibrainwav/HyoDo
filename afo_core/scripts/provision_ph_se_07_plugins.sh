#!/bin/bash
set -euo pipefail

# PH-SE-07: Advanced Visual Orchestration — plugin config provisioning
# This script provisions configuration stubs for Obsidian plugins to enforce
# Kingdom Standards (Colors, Layouts, Entry Points).

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
PLUGIN_DIR="$VAULT/.obsidian/plugins"

echo "🎨 Provisioning Visual Plugin Configs at: $VAULT"

mkdir -p "$VAULT/.obsidian/plugins/juggl" \
         "$VAULT/.obsidian/plugins/3d-graph" \
         "$VAULT/scripts"

# 1. Juggl Config (Truth=Blue, Goodness=Green, Beauty=Gold)
cat > "$VAULT/.obsidian/plugins/juggl/data.json" <<'JSON'
{
  "layout": "force",
  "animate": true,
  "nodeSize": "connections",
  "groups": [
    {
      "name": "MCP (Truth)",
      "color": "#0000FF",
      "query": "tag:#MCP"
    },
    {
      "name": "Skills (Goodness)",
      "color": "#008000",
      "query": "tag:#Skills"
    },
    {
      "name": "Context7 (Beauty)",
      "color": "#FFD700",
      "query": "tag:#Context7"
    }
  ]
}
JSON
echo "✅ Provisioned Juggl Config (Blue/Green/Gold)"

# 2. 3D Graph Config (Simple Stub)
cat > "$VAULT/.obsidian/plugins/3d-graph/data.json" <<'JSON'
{
  "zAxis": "date",
  "nodeRepulsion": 200,
  "showClusters": true
}
JSON
echo "✅ Provisioned 3D Graph Config"

# 3. Dataview Script (Graph Query Stub)
cat > "$VAULT/scripts/dv_graph.js" <<'JS'
/**
 * Dataview Graph Renderer
 * Usage: dv.view("scripts/dv_graph", { query: "#MCP" })
 */
const query = input.query || "";
dv.paragraph(`**Rendering Dynamic Graph for: ${query}**`);
// In a real setup, this would emit Juggl/Mermaid syntax
JS
echo "✅ Provisioned Dataview Script"

# 4. 00_HOME.canvas (Visual Entry Point)
# Simple Canvas with a link to 00_HOME.md
cat > "$VAULT/00_HOME.canvas" <<'JSON'
{
	"nodes": [
		{
			"id": "node1",
			"x": 0,
			"y": 0,
			"width": 400,
			"height": 400,
			"type": "file",
			"file": "00_HOME.md"
		},
		{
			"id": "node2",
			"x": 500,
			"y": 0,
			"width": 400,
			"height": 200,
			"type": "text",
			"text": "# AFO Kingdom Visual Entry\n\nDrag Phase Nodes here to expand."
		}
	],
	"edges": [
        {
            "id": "edge1",
            "fromNode": "node2",
            "fromSide": "left",
            "toNode": "node1",
            "toSide": "right"
        }
    ]
}
JSON
echo "✅ Provisioned 00_HOME.canvas"

echo "[ok] PH-SE-07 Visual Orchestration provisioned."
