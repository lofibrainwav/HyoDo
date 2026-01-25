#!/usr/bin/env bash
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
cd "${root}"

evidence="${1:-}"
if [ -z "${evidence}" ]; then
  evidence="$(ls -1dt docs/ssot/evidence/SSOT_LOCK_SYNC_GATE_* 2>/dev/null | head -1 || true)"
fi

if [ -z "${evidence}" ] || [ ! -d "${evidence}" ]; then
  echo "FAIL: evidence dir not found"
  exit 1
fi

hits_file="${evidence}/abs_path_hits.out.txt"
if [ ! -f "${hits_file}" ]; then
  echo "FAIL: ${hits_file} not found"
  exit 1
fi

ts="$(date +%Y%m%d_%H%M%S)"
workdir="docs/ssot/evidence/ABS_PATH_FIX_${ts}"
mkdir -p "${workdir}"

top20="${workdir}/top20_files.txt"
todo="${workdir}/todo_manual_fix.txt"
patched="${workdir}/patched_files.txt"

cut -d: -f1 "${hits_file}" | sort | uniq -c | sort -nr | head -20 > "${top20}"
: > "${todo}"
: > "${patched}"

python3 -c "
import os, re, pathlib, sys

root = pathlib.Path(os.popen('git rev-parse --show-toplevel').read().strip())
workdir = pathlib.Path('$workdir')
top20_file = workdir / 'top20_files.txt'
todo_file = workdir / 'todo_manual_fix.txt'
patched_file = workdir / 'patched_files.txt'

root_str = str(root)
pat_user_root = re.compile(r'/Users/[^/]+/AFO_Kingdom')
pat_root = re.compile(re.escape(root_str))

def read_text(p: pathlib.Path) -> str:
    return p.read_text(encoding='utf-8', errors='replace')

def write_text(p: pathlib.Path, s: str) -> None:
    p.write_text(s, encoding='utf-8')

def replace_in_file(path: pathlib.Path, repl: str, extra_pat=None) -> bool:
    s = read_text(path)
    s2 = pat_user_root.sub(repl, s)
    s2 = pat_root.sub(repl, s2)
    if extra_pat:
        s2 = extra_pat.sub(repl, s2)
    if s2 != s:
        write_text(path, s2)
        return True
    return False

def log(p: pathlib.Path, kind: str) -> None:
    with (patched_file if kind == 'patched' else todo_file).open('a', encoding='utf-8') as f:
        f.write(f'{kind}\t{p.as_posix()}\n')

lines = top20_file.read_text(encoding='utf-8').splitlines()
files = []
for ln in lines:
    ln = ln.strip()
    if not ln:
        continue
    parts = ln.split()
    if len(parts) < 2:
        continue
    files.append(parts[-1])

for fp in files:
    path = (root / fp).resolve()
    if not path.exists() or not path.is_file():
        log(pathlib.Path(fp), 'todo')
        continue

    rel = path.relative_to(root).as_posix()

    # .github workflows: github.workspace
    if rel.startswith('.github/workflows/') and rel.endswith(('.yml', '.yaml')):
        changed = replace_in_file(path, '\${{ github.workspace }}')
        log(path, 'patched' if changed else 'todo')
        continue

    # VS Code: workspaceFolder
    if rel.startswith('.vscode/') and rel.endswith('.json'):
        # also handle file:///Users/... patterns
        extra = re.compile(r'file:///Users/[^/]+/AFO_Kingdom')
        changed = replace_in_file(path, '\${workspaceFolder}', extra_pat=extra)
        log(path, 'patched' if changed else 'todo')
        continue

    # Shell scripts: use ROOT var pattern (keep suffix paths intact)
    if rel.startswith('scripts/') and rel.endswith(('.sh', '.bash', '.zsh')):
        s = read_text(path)
        if 'ROOT=' not in s:
            lines2 = s.splitlines()
            if lines2 and lines2[0].startswith('#!'):
                lines2.insert(1, 'ROOT=\"\$(git rev-parse --show-toplevel)\"')
            else:
                lines2.insert(0, 'ROOT=\"\$(git rev-parse --show-toplevel)\"')
            s = '\n'.join(lines2) + ('\n' if not s.endswith('\n') else '')
        s2 = pat_user_root.sub('\"\${ROOT}\"', s)
        s2 = pat_root.sub('\"\${ROOT}\"', s2)
        if s2 != s:
            write_text(path, s2)
            log(path, 'patched')
        else:
            log(path, 'todo')
        continue

    log(path, 'todo')

print('ABS_PATH fix completed')
"

PY
