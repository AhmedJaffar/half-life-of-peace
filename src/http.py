"""Cached, retrying HTTP helpers.

All network access in the project goes through :func:`get_json` so that
(a) responses are cached on disk, making runs resumable and the pipeline
reproducible offline, and (b) every request carries a descriptive
User-Agent, as the Wikimedia API requires.
"""

import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from . import config

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": config.USER_AGENT, "Accept": "application/json"})


def slug(text: str, maxlen: int = 80) -> str:
    """Filesystem-safe slug that is stable across platforms."""
    norm = unicodedata.normalize("NFKD", str(text))
    norm = norm.encode("ascii", "ignore").decode("ascii")
    norm = re.sub(r"[^A-Za-z0-9]+", "-", norm).strip("-").lower()
    return (norm or "x")[:maxlen]


def get_json(
    url: str,
    cache_path: Optional[Path] = None,
    retries: int = 5,
    timeout: int = 60,
) -> Optional[Dict[str, Any]]:
    """GET ``url`` as JSON, caching the result at ``cache_path``.

    Returns ``None`` for HTTP 404 (resource genuinely absent) so that callers
    can distinguish "no data" from "request failed".
    """
    if cache_path is not None:
        cache_path = Path(cache_path)
        if cache_path.exists():
            with cache_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)

    last_err = "unknown"
    for attempt in range(retries):
        try:
            resp = SESSION.get(url, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                if cache_path is not None:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    tmp = cache_path.with_suffix(cache_path.suffix + ".tmp")
                    with tmp.open("w", encoding="utf-8") as fh:
                        json.dump(data, fh)
                    tmp.replace(cache_path)
                return data
            if resp.status_code == 404:
                if cache_path is not None:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    with cache_path.open("w", encoding="utf-8") as fh:
                        json.dump({"_missing": True}, fh)
                return None
            last_err = "HTTP %s" % resp.status_code
        except Exception as exc:  # noqa: BLE001 - network layer is best-effort
            last_err = repr(exc)[:200]
        time.sleep(min(1.5 * (2 ** attempt), 20))
        last_err = last_err  # keep for message

    raise RuntimeError("GET failed after %d tries: %s (%s)" % (retries, url, last_err))
