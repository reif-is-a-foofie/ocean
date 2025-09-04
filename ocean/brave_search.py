from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx


BRAVE_ENDPOINT = os.getenv("BRAVE_SEARCH_ENDPOINT", "https://api.search.brave.com/res/v1/web/search")


def is_configured() -> bool:
    return bool(os.getenv("BRAVE_API_KEY"))


def search(query: str, count: int = 5, timeout: float = 8.0) -> Optional[Dict[str, Any]]:
    """Perform a Brave Search API query. Returns parsed JSON or None.

    Requires BRAVE_API_KEY in the environment. Uses minimal params and short timeout.
    """
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        return None
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": query,
        "count": max(1, min(count, 20)),
        "safesearch": "moderate",
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(BRAVE_ENDPOINT, headers=headers, params=params)
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


def summarize_results(data: Dict[str, Any], max_items: int = 5) -> str:
    """Return a compact Markdown summary for Brave results JSON."""
    out: List[str] = []
    web = (data or {}).get("web", {})
    results = web.get("results") if isinstance(web, dict) else None
    if not isinstance(results, list):
        return ""
    for item in results[:max_items]:
        try:
            title = str(item.get("title") or "(no title)")
            url = str(item.get("url") or "")
            snippet = str(item.get("description") or "")
            out.append(f"- [{title}]({url}) — {snippet}")
        except Exception:
            continue
    return "\n".join(out)

