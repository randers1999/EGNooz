from __future__ import annotations

import fcntl
import json
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from egnooz.config import Settings
from egnooz.edition import Edition

log = logging.getLogger("egnooz.store")


@contextmanager
def file_lock(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


class EditionStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        settings.ensure_dirs()

    def draft_path(self, edition_date: str) -> Path:
        return self.settings.drafts_dir / f"{edition_date}.json"

    def published_path(self, edition_date: str) -> Path:
        return self.settings.published_dir / f"{edition_date}.json"

    def latest_path(self) -> Path:
        return self.settings.published_dir / "latest.json"

    def load_draft(self, edition_date: str) -> Edition | None:
        path = self.draft_path(edition_date)
        if not path.is_file():
            return None
        return Edition.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def load_published(self, edition_date: str) -> Edition | None:
        path = self.published_path(edition_date)
        if not path.is_file():
            return None
        return Edition.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def load_latest(self) -> Edition | None:
        path = self.latest_path()
        if not path.is_file():
            return None
        return Edition.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def save_draft(self, edition: Edition) -> Path:
        path = self.draft_path(edition.edition_date)
        with file_lock(path.with_suffix(".json.lock")):
            _atomic_write(path, edition.to_draft_dict())
        log.info("Wrote draft %s", path)
        return path

    def save_published(self, edition: Edition) -> tuple[Path, Path]:
        dated = self.published_path(edition.edition_date)
        latest = self.latest_path()
        payload = edition.to_public_dict()
        with file_lock(dated.with_suffix(".json.lock")):
            _atomic_write(dated, payload)
            _atomic_write(latest, payload)
        log.info("Wrote published %s and %s", dated, latest)
        return dated, latest

    def is_published(self, edition_date: str) -> bool:
        return self.published_path(edition_date).is_file()

    def reminder_marker(self, edition_date: str) -> Path:
        return self.settings.state_dir / f"reminder-{edition_date}.sent"

    def mark_reminder_sent(self, edition_date: str) -> None:
        path = self.reminder_marker(edition_date)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("sent\n", encoding="utf-8")
