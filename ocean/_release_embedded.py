"""Release-only Gemini setup key (stub in public git).

Private release builds run ``scripts/embed_release_gemini_key.py`` before
``pip wheel`` / packaging so this module contains a non-empty
``EMBEDDED_GEMINI_SETUP_KEY``. Wheels and "compiled" bundles are still
extractable — this is convenience, not secrecy from a determined attacker.

Never commit a real key to a public repository.
"""

EMBEDDED_GEMINI_SETUP_KEY: str = ""
