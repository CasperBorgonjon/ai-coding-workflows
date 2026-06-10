#!/usr/bin/env bash
# Install the disciplined-build workflow into Claude Code, together with
# every professional skill its manifest declares, pinned to the declared refs.
#
#   ./install.sh            -> ~/.claude/skills  (available everywhere)
#   ./install.sh --project  -> ./.claude/skills  (this repo only)
#
# Idempotent: safe to re-run; each skill is replaced wholesale, so no stale
# files survive a pin bump. Fails loudly if any declared source is
# unreachable — never a silent partial install.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
MANIFEST="$ROOT/skills/disciplined-build/manifest.json"

DEST="$HOME/.claude/skills"
if [[ "${1:-}" == "--project" ]]; then
  DEST="$(pwd)/.claude/skills"
fi

for tool in git tar; do
  command -v "$tool" >/dev/null || { echo "error: '$tool' is required" >&2; exit 1; }
done
# Windows installs often expose Python as 'python' (Git Bash), not 'python3'
PYTHON="$(command -v python3 || command -v python || true)"
[[ -n "$PYTHON" ]] || { echo "error: python3 (or python) is required" >&2; exit 1; }
[[ -f "$MANIFEST" ]] || { echo "error: manifest not found at $MANIFEST" >&2; exit 1; }

CACHE="$(mktemp -d)"
trap 'rm -rf "$CACHE"' EXIT

# --- 1. the orchestrator itself (and its manifest) ---
mkdir -p "$DEST"
cp -R "$ROOT/skills/." "$DEST/"

# --- 2. every manifest-declared professional skill, pinned ---
# Lines of: name <TAB> source <TAB> path <TAB> ref  (deduped by name)
DEPS="$("$PYTHON" - "$MANIFEST" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
seen = set()
for step in data["steps"]:
    for s in step["skills"]:
        if s["name"] in seen:
            continue
        seen.add(s["name"])
        print("\t".join((s["name"], s["source"], s["path"], s["ref"])))
PY
)"

repo_for() {  # clone each unique source once into the cache
  local source="$1" key dir
  key="$(printf '%s' "$source" | cksum | cut -d' ' -f1)"
  dir="$CACHE/repo-$key"
  if [[ ! -d "$dir" ]]; then
    git clone --quiet "$source" "$dir" 2>/dev/null || {
      echo "error: cannot fetch $source — check the URL and your network" >&2
      exit 1
    }
  fi
  printf '%s' "$dir"
}

while IFS=$'\t' read -r name source path ref; do
  [[ -n "$name" ]] || continue
  repo="$(repo_for "$source")"
  git -C "$repo" cat-file -e "$ref^{commit}" 2>/dev/null || {
    echo "error: pinned ref $ref for skill '$name' not found in $source" >&2
    exit 1
  }
  extract="$CACHE/extract-$name"
  mkdir -p "$extract"
  git -C "$repo" archive "$ref" -- "$path" | tar -x -C "$extract"
  [[ -f "$extract/$path/SKILL.md" ]] || {
    echo "error: no SKILL.md at $path in $source@$ref (skill '$name')" >&2
    exit 1
  }
  rm -rf "${DEST:?}/$name"
  mkdir -p "$DEST/$name"
  cp -R "$extract/$path/." "$DEST/$name/"
  printf '%s\n' "$ref" > "$DEST/$name/.pinned-ref"
  echo "  pinned $name @ ${ref:0:12}  ($source)"
done <<< "$DEPS"

echo "Installed disciplined-build + manifest-declared skills into: $DEST"
echo "Start a feature in Claude Code with the 'disciplined-build' skill."
