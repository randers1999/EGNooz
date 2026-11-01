from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

def _phrase_pattern(name: str) -> re.Pattern[str]:
    parts = [re.escape(part) for part in name.split() if part]
    body = r"\s+".join(parts)
    return re.compile(rf"(?<![A-Za-z]){body}(?![A-Za-z])", re.IGNORECASE)


@dataclass
class PlaceFilter:
    include_names: list[str]
    exclude_names: list[str]
    _include: list[tuple[str, re.Pattern[str]]] = field(init=False, repr=False)
    _exclude: list[tuple[str, re.Pattern[str]]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        includes = sorted({n.strip() for n in self.include_names if n.strip()}, key=len, reverse=True)
        excludes = sorted({n.strip() for n in self.exclude_names if n.strip()}, key=len, reverse=True)
        self._include = [(name, _phrase_pattern(name)) for name in includes]
        self._exclude = [(name, _phrase_pattern(name)) for name in excludes]

    def matched_places(self, *parts: str | None) -> list[str]:
        blob = " ".join(p for p in parts if p)
        if not blob:
            return []
        found: list[str] = []
        seen: set[str] = set()
        for name, pattern in self._include:
            if pattern.search(blob) and name.lower() not in seen:
                seen.add(name.lower())
                found.append(name)
        return found

    def in_scope(self, *parts: str | None) -> bool:
        return bool(self.matched_places(*parts))

    def excluded_only(self, *parts: str | None) -> bool:
        """True when neighbour names appear and no in-scope place does."""
        if self.in_scope(*parts):
            return False
        blob = " ".join(p for p in parts if p)
        return any(pattern.search(blob) for _, pattern in self._exclude)


def load_place_filter(path: Path) -> PlaceFilter:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return PlaceFilter(
        include_names=list(data.get("include") or []),
        exclude_names=list(data.get("exclude") or []),
    )


@lru_cache(maxsize=8)
def place_filter_from(path: str) -> PlaceFilter:
    return load_place_filter(Path(path))
