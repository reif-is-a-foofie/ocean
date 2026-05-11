import subprocess
import sys
from pathlib import Path


def test_python_m_ocean_help():
    root = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [sys.executable, "-m", "ocean", "--help"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0
    assert "OCEAN CLI orchestrator" in r.stdout
