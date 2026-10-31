from __future__ import annotations

import logging

import httpx

log = logging.getLogger("egnooz.http")

DEFAULT_USER_AGENT = (
    "EGNooz/0.1 (+https://github.com/randers1999/EGNooz; East Gippsland daily briefing)"
)


class FetchError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def fetch_bytes(
    url: str,
    *,
    user_agent: str = DEFAULT_USER_AGENT,
    timeout: float = 20.0,
    max_bytes: int = 2_000_000,
    accept: str = "*/*",
) -> tuple[int, bytes, str]:
    headers = {
        "User-Agent": user_agent,
        "Accept": accept,
        "Accept-Language": "en-AU,en;q=0.8",
    }
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
            response = client.get(url)
    except httpx.HTTPError as exc:
        raise FetchError(f"Request failed: {exc}") from exc
    if response.status_code >= 400:
        raise FetchError(
            f"HTTP {response.status_code} for {url}",
            status_code=response.status_code,
        )
    content = response.content
    if len(content) > max_bytes:
        content = content[:max_bytes]
    content_type = response.headers.get("content-type", "")
    return response.status_code, content, content_type
