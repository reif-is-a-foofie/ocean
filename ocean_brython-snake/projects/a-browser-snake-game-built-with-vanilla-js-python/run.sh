#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Create venv if missing
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate

# Install deps for backend if present
if [ -d backend ]; then
  python -m pip install --upgrade pip >/dev/null
  pip install fastapi[all] uvicorn >/dev/null
fi

# Start backend
if [ -d backend ]; then
  (uvicorn backend.app:app --host 127.0.0.1 --port 8000 &)
  BACK_PID=$!
  echo "Backend: http://127.0.0.1:8000/healthz (pid $BACK_PID)"
fi

# Serve UI if present
if [ -d ui ]; then
  python -m http.server 5173 -d ui &
  UI_PID=$!
  echo "UI: http://127.0.0.1:5173 (pid $UI_PID)"
fi

wait
