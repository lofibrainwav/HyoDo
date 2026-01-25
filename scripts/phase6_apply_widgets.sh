#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

pick_next_dir() {
  python3 - <<'PY'
import json, pathlib, sys
root = pathlib.Path(".")
cands=[]
for pj in root.rglob("package.json"):
    try:
        data=json.loads(pj.read_text(encoding="utf-8"))
    except Exception:
        continue
    deps=(data.get("dependencies") or {}) | (data.get("devDependencies") or {})
    if "next" in deps:
        cands.append(str(pj.parent))
cands=sorted(set(cands))
if len(cands)==1:
    print(cands[0])
    sys.exit(0)
print("MULTI", *cands, sep="\n")
sys.exit(2)
PY
}

NEXT_APP_DIR="${NEXT_APP_DIR:-}"
if [ -z "${NEXT_APP_DIR}" ]; then
  out="$(pick_next_dir || true)"
  if echo "$out" | head -n1 | grep -q '^MULTI$'; then
    echo "❌ Next.js 프로젝트가 여러 개입니다. 아래 중 하나를 NEXT_APP_DIR로 지정해주세요:"
    echo "$out" | tail -n +2
    echo
    echo "예) NEXT_APP_DIR='packages/trinity-dashboard' bash scripts/phase6_apply_widgets.sh"
    exit 2
  fi
  NEXT_APP_DIR="$out"
fi

if [ ! -d "$NEXT_APP_DIR" ]; then
  echo "❌ NEXT_APP_DIR not found: $NEXT_APP_DIR"
  exit 2
fi

BASE_DIR="$NEXT_APP_DIR"
SRC_DIR="$BASE_DIR"
if [ -d "$BASE_DIR/src" ]; then
  SRC_DIR="$BASE_DIR/src"
fi

APP_DIR=""
if [ -d "$SRC_DIR/app" ]; then
  APP_DIR="$SRC_DIR/app"
elif [ -d "$BASE_DIR/app" ]; then
  APP_DIR="$BASE_DIR/app"
fi

WIDGET_ROOT="$SRC_DIR/components/widgets"
HOOK_ROOT="$SRC_DIR/hooks"
mkdir -p "$WIDGET_ROOT" "$HOOK_ROOT"

cat > "$HOOK_ROOT/useWidget.ts" <<'TS'
import { useEffect, useMemo, useState } from "react";

type UseWidgetState<T> = {
  data: T | null;
  error: string | null;
  loading: boolean;
  refreshedAt: number | null;
};

function buildUrl(path: string): string {
  const base = process.env.NEXT_PUBLIC_AFO_API_BASE || "http://localhost:8010";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

export function useWidget<T>(path: string, refreshMs = 5000) {
  const url = useMemo(() => buildUrl(path), [path]);
  const [state, setState] = useState<UseWidgetState<T>>({
    data: null,
    error: null,
    loading: true,
    refreshedAt: null,
  });

  useEffect(() => {
    let alive = true;

    const run = async () => {
      try {
        const res = await fetch(url, { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = (await res.json()) as T;
        if (!alive) return;
        setState({ data: json, error: null, loading: false, refreshedAt: Date.now() });
      } catch (e) {
        if (!alive) return;
        const msg = e instanceof Error ? e.message : "unknown error";
        setState((prev) => ({ ...prev, error: msg, loading: false, refreshedAt: Date.now() }));
      }
    };

    run();
    const id = window.setInterval(run, refreshMs);
    return () => {
      alive = false;
      window.clearInterval(id);
    };
  }, [url, refreshMs]);

  return state;
}
TS

cat > "$WIDGET_ROOT/GenericWidget.tsx" <<'TSX'
type Props = {
  title: string;
  status?: "GREEN" | "YELLOW" | "RED";
  subtitle?: string;
  children: React.ReactNode;
};

export default function GenericWidget({ title, status, subtitle, children }: Props) {
  const badge =
    status === "GREEN" ? "✅" : status === "YELLOW" ? "🟡" : status === "RED" ? "⛔" : "•";

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 shadow-lg backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">{title}</div>
          {subtitle ? <div className="mt-1 text-xs opacity-70">{subtitle}</div> : null}
        </div>
        <div className="text-sm">{badge}</div>
      </div>
      <div className="mt-3">{children}</div>
    </div>
  );
}
TSX

cat > "$WIDGET_ROOT/HealthWidget.tsx" <<'TSX'
import GenericWidget from "./GenericWidget";
import { useWidget } from "../../hooks/useWidget";

type Health = {
  status?: string;
  score?: number;
  organs_v2?: Record<string, unknown>;
  organs?: Record<string, unknown>;
};

export default function HealthWidget() {
  const { data, error, loading, refreshedAt } = useWidget<Health>("/api/health/comprehensive", 5000);

  const organsCount =
    data?.organs_v2 ? Object.keys(data.organs_v2).length : data?.organs ? Object.keys(data.organs).length : 0;

  const score = typeof data?.score === "number" ? data.score : null;

  const status: "GREEN" | "YELLOW" | "RED" | undefined =
    error ? "RED" : score !== null ? (score >= 90 ? "GREEN" : score >= 75 ? "YELLOW" : "RED") : undefined;

  return (
    <GenericWidget
      title="Health"
      status={status}
      subtitle={loading ? "loading..." : error ? `error: ${error}` : `refreshed: ${refreshedAt ? new Date(refreshedAt).toLocaleTimeString() : "-"}`}
    >
      <div className="text-sm">
        <div>Organs: {organsCount}</div>
        <div>Score: {score !== null ? score.toFixed(1) : "-"}</div>
      </div>
    </GenericWidget>
  );
}
TSX

cat > "$WIDGET_ROOT/SkillsWidget.tsx" <<'TSX'
import GenericWidget from "./GenericWidget";
import { useWidget } from "../../hooks/useWidget";

type Skills = { skills?: unknown[]; total?: number };

export default function SkillsWidget() {
  const { data, error, loading } = useWidget<Skills>("/api/skills", 7000);
  const count =
    typeof data?.total === "number" ? data.total : Array.isArray(data?.skills) ? data!.skills!.length : 0;

  const status: "GREEN" | "YELLOW" | "RED" | undefined = error ? "RED" : count > 0 ? "GREEN" : loading ? undefined : "YELLOW";

  return (
    <GenericWidget title="Skills" status={status} subtitle={loading ? "loading..." : error ? `error: ${error}` : ""}>
      <div className="text-sm">Total Skills: {count}</div>
    </GenericWidget>
  );
}
TSX

cat > "$WIDGET_ROOT/Context7Widget.tsx" <<'TSX'
import GenericWidget from "./GenericWidget";
import { useWidget } from "../../hooks/useWidget";

type Item = { category?: string };
type Payload = { items?: Item[]; total?: number };

export default function Context7Widget() {
  const { data, error, loading } = useWidget<Payload>("/api/context7/list", 10000);

  const items = Array.isArray(data?.items) ? data!.items! : [];
  const total = typeof data?.total === "number" ? data.total : items.length;

  const categories = items.reduce<Record<string, number>>((acc, it) => {
    const k = it.category || "Uncategorized";
    acc[k] = (acc[k] || 0) + 1;
    return acc;
  }, {});

  const top = Object.entries(categories)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  const status: "GREEN" | "YELLOW" | "RED" | undefined = error ? "RED" : total >= 9 ? "GREEN" : loading ? undefined : "YELLOW";

  return (
    <GenericWidget title="Context7" status={status} subtitle={loading ? "loading..." : error ? `error: ${error}` : ""}>
      <div className="text-sm">Items: {total}</div>
      <div className="mt-2 text-xs opacity-80">
        {top.length ? top.map(([k, v]) => `${k}:${v}`).join(" · ") : "categories: -"}
      </div>
    </GenericWidget>
  );
}
TSX

cat > "$WIDGET_ROOT/SyncWidget.tsx" <<'TSX'
import GenericWidget from "./GenericWidget";
import { useWidget } from "../../hooks/useWidget";

type Health = { status?: string; score?: number };

export default function SyncWidget() {
  const { data, error, loading } = useWidget<Health>("/api/health/comprehensive", 12000);
  const score = typeof data?.score === "number" ? data.score : null;

  const status: "GREEN" | "YELLOW" | "RED" | undefined =
    error ? "RED" : score !== null ? (score >= 90 ? "GREEN" : score >= 75 ? "YELLOW" : "RED") : undefined;

  return (
    <GenericWidget title="Sync" status={status} subtitle={loading ? "loading..." : error ? `error: ${error}` : ""}>
      <div className="text-sm">
        <div>Local API: {error ? "DOWN" : "OK"}</div>
        <div>Seal: {status === "GREEN" ? "Double Green" : status === "YELLOW" ? "Stable" : "Investigate"}</div>
      </div>
    </GenericWidget>
  );
}
TSX

TARGET_PAGE=""
if [ -n "$APP_DIR" ]; then
  for p in "$APP_DIR/royal/page.tsx" "$APP_DIR/dashboard/page.tsx"; do
    if [ -f "$p" ]; then TARGET_PAGE="$p"; break; fi
  done
fi

if [ -n "$TARGET_PAGE" ]; then
  python3 - <<PY
from pathlib import Path
p=Path("$TARGET_PAGE")
s=p.read_text(encoding="utf-8")

# Check imports, robustly
imports_block = ""
if "/components/widgets/HealthWidget" not in s:
    imports_block += 'import HealthWidget from "../../components/widgets/HealthWidget";\\n'
if "/components/widgets/SkillsWidget" not in s:
    imports_block += 'import SkillsWidget from "../../components/widgets/SkillsWidget";\\n'
if "/components/widgets/Context7Widget" not in s:
    imports_block += 'import Context7Widget from "../../components/widgets/Context7Widget";\\n'
if "/components/widgets/SyncWidget" not in s:
    imports_block += 'import SyncWidget from "../../components/widgets/SyncWidget";\\n'

if imports_block:
    # Insert after last import or at top
    if "import " in s:
        last_import = s.rfind("import ")
        newline = s.find("\\n", last_import)
        s = s[:newline+1] + imports_block + s[newline+1:]
    else:
        s = imports_block + "\\n" + s

marker = "__AFO_WIDGET_GRID__"
grid = f"""
<div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2" data-afo="{marker}">
  <HealthWidget />
  <SkillsWidget />
  <Context7Widget />
  <SyncWidget />
</div>
"""

if marker in s:
    print("grid already present:", p)
else:
    # Insert before closing main, or at end
    if "</main>" in s:
        s = s.replace("</main>", grid + "\\n</main>", 1)
    else:
        s += "\\n" + grid + "\\n"

p.write_text(s, encoding="utf-8")
print("✅ patched page:", p)
PY
else
  echo "✅ widgets created."
  echo "ℹ️ page patch skipped (royal/dashboard page not found)."
fi

echo
echo "✅ Phase 6 Action 2 scaffold done."
