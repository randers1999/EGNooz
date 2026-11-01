from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    home: str
    match: str
    ingest: str
    enabled: bool
    feed_url: str | None = None
    lookback_hours: int = 48
    notes: str = ""

    @property
    def is_local(self) -> bool:
        return self.match == "local"

    @property
    def default_included(self) -> bool:
        return self.match == "local"

    @property
    def auto_fetch(self) -> bool:
        return self.enabled and self.ingest in {"rss", "json"} and bool(self.feed_url)


def _as_source(raw: dict) -> Source:
    lookback = raw.get("lookback_hours")
    if lookback is None:
        lookback = 36 if raw.get("match") == "mention" else 48
    notes = raw.get("notes") or ""
    if isinstance(notes, str):
        notes = " ".join(notes.split())
    return Source(
        id=str(raw["id"]),
        name=str(raw["name"]),
        home=str(raw.get("home") or ""),
        match=str(raw.get("match") or "local"),
        ingest=str(raw.get("ingest") or "none"),
        enabled=bool(raw.get("enabled", False)),
        feed_url=raw.get("feed_url"),
        lookback_hours=int(lookback),
        notes=notes,
    )


@dataclass
class SourceList:
    user_agent: str
    sources: list[Source]

    def by_id(self, source_id: str) -> Source | None:
        for source in self.sources:
            if source.id == source_id:
                return source
        return None

    def enabled(self) -> list[Source]:
        return [s for s in self.sources if s.enabled]


def load_sources(path: Path) -> SourceList:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    user_agent = data.get("user_agent") or (
        "EGNooz/0.1 (+https://github.com/randers1999/EGNooz; East Gippsland daily briefing)"
    )
    sources = [_as_source(item) for item in data.get("sources") or []]
    return SourceList(user_agent=user_agent, sources=sources)
