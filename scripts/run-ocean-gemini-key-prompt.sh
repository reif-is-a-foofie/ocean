#!/usr/bin/env bash
# Point Ocean at Gemini API and open `ocean chat` so it can prompt for GEMINI_API_KEY (hidden).
# Requires a real terminal (stdin + stdout TTY) for getpass.
#
# Notes:
# - docs/ocean_prefs.json is updated to codegen_backend=gemini_api (merge with existing prefs).
# - Shell-exported GEMINI_API_KEY / GOOGLE_API_KEY are dropped for this launch only.
# - If your workspace .env already defines GEMINI_API_KEY, remove or comment that line first,
#   or Ocean will load it and skip the prompt.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x "$ROOT/venv/bin/python" ]]; then
  PY="$ROOT/venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi

"$PY" - <<'PY'
import json
from pathlib import Path

p = Path("docs/ocean_prefs.json")
data = {}
if p.exists():
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
data["codegen_backend"] = "gemini_api"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print("ocean_prefs: set codegen_backend → gemini_api")
PY

echo "Launching ocean chat (Gemini). You should see: GEMINI_API_KEY (input hidden):"
exec env -u GEMINI_API_KEY -u GOOGLE_API_KEY "$PY" -m ocean chat "$@"
