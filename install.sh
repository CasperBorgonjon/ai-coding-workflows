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
PROJECT_DIR=""
if [[ "${1:-}" == "--project" ]]; then
  DEST="$(pwd)/.claude/skills"
  PROJECT_DIR="$(pwd)"
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

# --- 3. the shared context source (optional, project-scoped) ---
# A workflow may inherit one team glossary: a CONTEXT.md fetched from a pinned
# git repo, declared as a top-level "sharedContext" block in the manifest:
#   "sharedContext": { "source": <git url>, "path": <dir holding CONTEXT.md>, "ref": <full SHA> }
# It lands in the *project* at .workflow/shared/CONTEXT.md (pinned, read-only) —
# never in the skills dir. It is only meaningful against a specific codebase, so
# it is fetched on a --project install and skipped (cleanly, not an error) on a
# bare global install. A manifest with no sharedContext key behaves as before.
CTX="$("$PYTHON" - "$MANIFEST" <<'PY'
import json, sys
c = json.load(open(sys.argv[1])).get("sharedContext")
if c:
    missing = [k for k in ("source", "ref") if not c.get(k)]
    if missing:
        sys.exit("error: sharedContext is missing required key(s): " + ", ".join(missing))
    print("\t".join((c["source"], c.get("path", "."), c["ref"])))
PY
)"

if [[ -n "$CTX" ]]; then
  if [[ -z "$PROJECT_DIR" ]]; then
    echo "  shared context declared — skipped (no project; re-run with --project inside a repo)"
  else
    IFS=$'\t' read -r c_source c_path c_ref <<< "$CTX"
    repo="$(repo_for "$c_source")"
    git -C "$repo" cat-file -e "$c_ref^{commit}" 2>/dev/null || {
      echo "error: pinned ref $c_ref for shared context not found in $c_source" >&2
      exit 1
    }
    extract="$CACHE/extract-shared-context"
    mkdir -p "$extract"
    git -C "$repo" archive "$c_ref" -- "$c_path" | tar -x -C "$extract"
    [[ -f "$extract/$c_path/CONTEXT.md" ]] || {
      echo "error: no CONTEXT.md at $c_path in $c_source@$c_ref (shared context)" >&2
      exit 1
    }
    shared="$PROJECT_DIR/.workflow/shared"
    rm -rf "${shared:?}"  # guard: never rm -rf an empty path (mirrors the skill loop)
    mkdir -p "$shared"
    cp "$extract/$c_path/CONTEXT.md" "$shared/CONTEXT.md"
    printf '%s\n' "$c_ref" > "$shared/.pinned-ref"
    echo "  pinned shared context @ ${c_ref:0:12}  ($c_source)"
  fi
fi

echo "Installed disciplined-build + manifest-declared skills into: $DEST"
echo "Start a feature in Claude Code with the 'disciplined-build' skill."
