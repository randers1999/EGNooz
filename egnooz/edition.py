from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any

from egnooz import EDITOR_NOTE_MAX, SCHEMA_VERSION, TIMEZONE_NAME


def _clip_note(note: str | None) -> str:
    text = (note or "").strip()
    if len(text) > EDITOR_NOTE_MAX:
        return text[:EDITOR_NOTE_MAX]
    return text


@dataclass
class NewsItem:
    id: str
    title: str
    url: str
    source_id: str
    source_name: str
    published_at: str | None
    snippet: str
    match_reason: str
    matched_places: list[str] = field(default_factory=list)
    included: bool = True

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "sourceId": self.source_id,
            "sourceName": self.source_name,
            "publishedAt": self.published_at,
            "snippet": self.snippet,
            "matchReason": self.match_reason,
            "matchedPlaces": list(self.matched_places),
        }

    def to_draft_dict(self) -> dict[str, Any]:
        data = self.to_public_dict()
        data["included"] = self.included
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewsItem":
        return cls(
            id=data["id"],
            title=data.get("title") or "",
            url=data.get("url") or "",
            source_id=data.get("sourceId") or data.get("source_id") or "",
            source_name=data.get("sourceName") or data.get("source_name") or "",
            published_at=data.get("publishedAt") or data.get("published_at"),
            snippet=data.get("snippet") or "",
            match_reason=data.get("matchReason") or data.get("match_reason") or "local-source",
            matched_places=list(data.get("matchedPlaces") or data.get("matched_places") or []),
            included=bool(data.get("included", True)),
        )


@dataclass
class WarningItem:
    id: str
    title: str
    url: str
    location: str
    category: str
    status: str
    updated_at: str | None
    feed_type: str
    matched_places: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "location": self.location,
            "category": self.category,
            "status": self.status,
            "updatedAt": self.updated_at,
            "feedType": self.feed_type,
            "matchedPlaces": list(self.matched_places),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WarningItem":
        return cls(
            id=str(data.get("id") or ""),
            title=data.get("title") or "",
            url=data.get("url") or "",
            location=data.get("location") or "",
            category=data.get("category") or "",
            status=data.get("status") or "",
            updated_at=data.get("updatedAt") or data.get("updated_at"),
            feed_type=data.get("feedType") or data.get("feed_type") or "incident",
            matched_places=list(data.get("matchedPlaces") or data.get("matched_places") or []),
        )


@dataclass
class IngestLogEntry:
    source_id: str
    status: str
    item_count: int = 0
    error: str | None = None
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourceId": self.source_id,
            "status": self.status,
            "itemCount": self.item_count,
            "error": self.error,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IngestLogEntry":
        return cls(
            source_id=data.get("sourceId") or data.get("source_id") or "",
            status=data.get("status") or "",
            item_count=int(data.get("itemCount") or data.get("item_count") or 0),
            error=data.get("error"),
            detail=data.get("detail"),
        )


def empty_warnings() -> dict[str, Any]:
    return {
        "source": "VicEmergency",
        "attribution": "Data from the State of Victoria, Australia.",
        "attributionUrl": (
            "https://www.emv.vic.gov.au/responsibilities/victorias-warning-system/emergency-data"
        ),
        "license": "CC BY 3.0 AU",
        "disclaimer": (
            "EGNooz is not an emergency service. For warnings use VicEmergency."
        ),
        "feedLastUpdated": None,
        "fetchedAt": None,
        "districtFireDanger": None,
        "districtTotalFireBan": None,
        "items": [],
    }


@dataclass
class Edition:
    edition_date: str
    status: str = "draft"
    schema_version: int = SCHEMA_VERSION
    timezone: str = TIMEZONE_NAME
    generated_at: str | None = None
    published_at: str | None = None
    editor_note: str = ""
    warnings: dict[str, Any] = field(default_factory=empty_warnings)
    items: list[NewsItem] = field(default_factory=list)
    ingest_log: list[IngestLogEntry] = field(default_factory=list)

    def included_items(self) -> list[NewsItem]:
        return [item for item in self.items if item.included]

    def counts(self) -> dict[str, int]:
        local = [i for i in self.items if i.match_reason == "local-source"]
        mention = [i for i in self.items if i.match_reason == "mention"]
        manual = [i for i in self.items if i.match_reason == "manual"]
        return {
            "total": len(self.items),
            "included": len(self.included_items()),
            "local": len(local),
            "mention": len(mention),
            "manual": len(manual),
            "warnings": len(self.warnings.get("items") or []),
        }

    def set_editor_note(self, note: str | None) -> None:
        self.editor_note = _clip_note(note)

    def to_draft_dict(self) -> dict[str, Any]:
        warnings = dict(self.warnings)
        warning_items = []
        for item in warnings.get("items") or []:
            if isinstance(item, WarningItem):
                warning_items.append(item.to_dict())
            else:
                warning_items.append(item)
        warnings["items"] = warning_items
        return {
            "schemaVersion": self.schema_version,
            "timezone": self.timezone,
            "editionDate": self.edition_date,
            "status": self.status,
            "generatedAt": self.generated_at,
            "publishedAt": self.published_at,
            "editorNote": self.editor_note,
            "warnings": warnings,
            "items": [item.to_draft_dict() for item in self.items],
            "ingestLog": [entry.to_dict() for entry in self.ingest_log],
        }

    def to_public_dict(self) -> dict[str, Any]:
        warnings = dict(self.warnings)
        warning_items = []
        for item in warnings.get("items") or []:
            if isinstance(item, WarningItem):
                warning_items.append(item.to_dict())
            else:
                warning_items.append(item)
        warnings["items"] = warning_items
        return {
            "schemaVersion": self.schema_version,
            "timezone": self.timezone,
            "editionDate": self.edition_date,
            "status": "published",
            "generatedAt": self.generated_at,
            "publishedAt": self.published_at,
            "editorNote": self.editor_note,
            "warnings": warnings,
            "items": [item.to_public_dict() for item in self.included_items()],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Edition":
        warnings = data.get("warnings") or empty_warnings()
        raw_items = warnings.get("items") or []
        parsed_warnings = []
        for item in raw_items:
            if isinstance(item, dict):
                parsed_warnings.append(WarningItem.from_dict(item).to_dict())
            else:
                parsed_warnings.append(item)
        warnings = dict(warnings)
        warnings["items"] = parsed_warnings
        return cls(
            edition_date=data.get("editionDate") or data.get("edition_date") or "",
            status=data.get("status") or "draft",
            schema_version=int(data.get("schemaVersion") or data.get("schema_version") or SCHEMA_VERSION),
            timezone=data.get("timezone") or TIMEZONE_NAME,
            generated_at=data.get("generatedAt") or data.get("generated_at"),
            published_at=data.get("publishedAt") or data.get("published_at"),
            editor_note=_clip_note(data.get("editorNote") or data.get("editor_note") or ""),
            warnings=warnings,
            items=[NewsItem.from_dict(item) for item in data.get("items") or []],
            ingest_log=[
                IngestLogEntry.from_dict(entry) for entry in data.get("ingestLog") or data.get("ingest_log") or []
            ],
        )


# Keep dataclass import used if we later introspect fields.
_ = asdict, fields
