#!/usr/bin/env bash
# Run the full test suite. No interactive input, no network, no credentials.
set -euo pipefail
cd "$(dirname "$0")"

python3 -m unittest discover -s tests -v
