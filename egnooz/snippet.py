from __future__ import annotations

import html as html_lib
import re
from html.parser import HTMLParser

from egnooz import SNIPPET_MAX

_WHITESPACE = re.compile(r"\s+")


class _StripTags(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"p", "br", "div", "li", "h1", "h2", "h3"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"p", "div", "li", "h1", "h2", "h3"}:
            self.parts.append(" ")

    def handle_entityref(self, name: str) -> None:
        self.parts.append(html_lib.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        self.parts.append(html_lib.unescape(f"&#{name};"))


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    parser = _StripTags()
    try:
        parser.feed(value)
        parser.close()
        text = "".join(parser.parts)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", value)
    text = html_lib.unescape(text)
    return _WHITESPACE.sub(" ", text).strip()


def make_snippet(value: str | None, limit: int = SNIPPET_MAX) -> str:
    text = strip_html(value)
    for suffix in ("Read more", "Continue reading", "Continue Reading"):
        if text.endswith(suffix):
            text = text[: -len(suffix)].rstrip(" .…")
    if len(text) <= limit:
        return text
    clipped = text[: limit - 1].rsplit(" ", 1)[0] or text[: limit - 1]
    return clipped.rstrip(".,;:") + "…"
