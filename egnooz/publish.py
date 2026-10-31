from __future__ import annotations

import logging

from egnooz.config import Settings
from egnooz.edition import Edition
from egnooz.store import EditionStore
from egnooz.timeutil import isoformat, now_melbourne

log = logging.getLogger("egnooz.publish")


class PublishError(RuntimeError):
    pass


def publish_edition(settings: Settings, edition: Edition, *, send_email: bool = True) -> Edition:
    if not edition.items and not (edition.warnings.get("items") or []):
        # Thin days are allowed, including an empty list.
        log.info("Publishing a thin edition for %s", edition.edition_date)
    edition.status = "published"
    edition.published_at = isoformat(now_melbourne())
    store = EditionStore(settings)
    store.save_draft(edition)
    store.save_published(edition)
    log.info(
        "Published %s (%s included items, %s warnings)",
        edition.edition_date,
        len(edition.included_items()),
        len(edition.warnings.get("items") or []),
    )
    if send_email:
        from egnooz.emailer import send_edition

        send_edition(settings, edition)
    return edition
