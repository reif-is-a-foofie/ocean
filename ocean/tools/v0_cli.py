import shutil
from typing import Optional


class V0Cli:
    """Lightweight adapter for the V0 CLI (if installed). Uses only availability checks.

    Cursor can expand this to call actual commands to generate UI assets.
    """

    @staticmethod
    def is_available() -> bool:
        return shutil.which("v0") is not None

    @staticmethod
    def version() -> Optional[str]:
        # Cursor can implement shell call to `v0 --version` if desired
        return None

