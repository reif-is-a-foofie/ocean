import os
import shutil
import subprocess

import pytest


CODex = shutil.which("codex")


@pytest.mark.skipif(CODex is None, reason="codex CLI not found on PATH")
@pytest.mark.skipif(os.getenv("OCEAN_TEST_CODEX") not in ("1", "true", "True"), reason="set OCEAN_TEST_CODEX=1 to run Codex E2E test")
def test_codex_e2e_exec_trivial():
    """End-to-end sanity check: codex exec returns trivial JSON.

    This ensures subscription/API auth and the exec path are operational.
    Skips if codex is not installed.
    """
    # If not authenticated and no API key, provide a clear skip reason
    try:
        out = subprocess.run([CODex, "auth"], capture_output=True, text=True, timeout=8)
        auth_txt = (out.stdout or out.stderr or "").lower()
        logged_in = any(k in auth_txt for k in ("logged in", "authenticated", "already logged"))
    except Exception:
        logged_in = False

    if not logged_in and not os.getenv("OPENAI_API_KEY"):
        pytest.skip("codex not authenticated and no OPENAI_API_KEY set")

    from ocean.cli import _codex_e2e_test, _warmup_codex

    # Warm up quickly to set OCEAN_CODEX_AUTH when subscription is ready
    _warmup_codex(timeout=10)
    ok, detail = _codex_e2e_test(timeout=12)
    assert ok, f"codex e2e failed: {detail}"
