#!/usr/bin/env bash
# Install the disciplined-build workflow skill into Claude Code.
#   ./install.sh            -> ~/.claude/skills  (available everywhere)
#   ./install.sh --project  -> ./.claude/skills  (this repo only)
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/skills"

if [[ "${1:-}" == "--project" ]]; then
  DEST="$(pwd)/.claude/skills"
else
  DEST="$HOME/.claude/skills"
fi

mkdir -p "$DEST"
cp -R "$SRC/." "$DEST/"

echo "Installed disciplined-build into: $DEST"
echo "Start a feature in Claude Code with the 'disciplined-build' skill."
