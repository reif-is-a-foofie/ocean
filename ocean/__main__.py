"""Support ``python3 -m ocean`` when the ``ocean`` console script is not on PATH."""

from __future__ import annotations

import sys


def main() -> None:
    try:
        from ocean.cli import entrypoint
    except ImportError as exc:
        print(
            "Ocean’s CLI dependencies are not installed yet.\n"
            "From this repository root run:\n\n"
            "  python3 -m pip install -e .\n\n"
            "Then use either:\n"
            "  ocean              # if venv/bin is on your PATH\n"
            "  python3 -m ocean   # always works from the repo after install\n",
            file=sys.stderr,
        )
        raise SystemExit(127) from exc
    entrypoint()


if __name__ == "__main__":
    main()
