#!/usr/bin/env bash
set -euo pipefail

RECORD_FILE="${1:-}"

if ! command -v mitmdump >/dev/null 2>&1; then
  echo "Error: mitmdump not found. Install with: brew install mitmproxy"
  exit 1
fi

if [ -z "$RECORD_FILE" ]; then
  echo "Usage: $(basename "$0") /path/to/recording.mitm"
  exit 1
fi

if [ ! -f "$RECORD_FILE" ]; then
  echo "Error: recording file not found: $RECORD_FILE"
  exit 1
fi

echo "Replaying from: $RECORD_FILE"
echo "Make sure your system proxy is set to 127.0.0.1:8080 before using the frontend."
echo "Stop replay with Ctrl+C."

mitmdump -p 8080 --server-replay "$RECORD_FILE"

