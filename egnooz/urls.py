from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_TRACKING = {"fbclid", "gclid", "mc_cid", "mc_eid", "igshid"}


def canonical_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    query_pairs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in _TRACKING:
            continue
        query_pairs.append((key, value))
    query = urlencode(query_pairs, doseq=True)
    return urlunparse((scheme, netloc, path, "", query, ""))


def item_id(source_id: str, url: str) -> str:
    digest = hashlib.sha256(f"{source_id}|{canonical_url(url)}".encode()).hexdigest()[:12]
    safe_source = re.sub(r"[^a-z0-9-]+", "-", source_id.lower()).strip("-")
    return f"{safe_source}-{digest}"


def hostname(url: str) -> str:
    return urlparse(url).netloc.lower().lstrip("www.")
