#!/usr/bin/env bash
# Install the disciplined-build workflow without cloning the repo yourself:
#
#   curl -fsSL https://raw.githubusercontent.com/CasperBorgonjon/ai-coding-workflows/main/bootstrap.sh | bash
#   curl -fsSL .../bootstrap.sh | bash -s -- --project   # project-local install
#
# Clones the repo into a temp dir, runs install.sh from there, cleans up.
set -euo pipefail

REPO="${DW_REPO:-https://github.com/CasperBorgonjon/ai-coding-workflows}"

command -v git >/dev/null || { echo "error: 'git' is required" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Fetching $REPO ..."
git clone --quiet --depth 1 "$REPO" "$TMP/repo" || {
  echo "error: cannot clone $REPO — check your network" >&2
  exit 1
}

"$TMP/repo/install.sh" "$@"
