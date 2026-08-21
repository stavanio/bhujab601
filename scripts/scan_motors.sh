#!/usr/bin/env bash
set -euo pipefail

CHANNEL="${1:-can0}"

uv run motorbridge-cli scan \
  --vendor robstride \
  --channel "$CHANNEL" \
  --start-id 1 \
  --end-id 7
