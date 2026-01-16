#!/usr/bin/env bash
set -euo pipefail

BACKEND_DIR="/Users/zhangxiaowen/Desktop/LlamaReportPro/llamareport-test/backend"
RECORD_DIR="${HOME}/llama_recordings"

if ! command -v mitmdump >/dev/null 2>&1; then
  echo "Error: mitmdump not found. Install with: brew install mitmproxy"
  exit 1
fi

if [ ! -d "$BACKEND_DIR" ]; then
  echo "Error: backend directory not found: $BACKEND_DIR"
  exit 1
fi

mkdir -p "$RECORD_DIR"
RECORD_FILE="${RECORD_DIR}/llama_recording_$(date +%Y%m%d_%H%M%S).mitm"

pushd "$BACKEND_DIR" >/dev/null
python main.py &
BACKEND_PID=$!
popd >/dev/null

cleanup() {
  if ps -p "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID"
  fi
}
trap cleanup EXIT INT TERM

echo "Recording to: $RECORD_FILE"
echo "Make sure your system proxy is set to 127.0.0.1:8080 before using the frontend."
echo "Stop recording with Ctrl+C."

mitmdump -p 8080 -w "$RECORD_FILE"

