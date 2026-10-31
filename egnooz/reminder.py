from __future__ import annotations

import logging
from datetime import date

from egnooz.config import Settings
from egnooz.store import EditionStore
from egnooz.timeutil import today_melbourne

log = logging.getLogger("egnooz.reminder")


def run_reminder(
    settings: Settings,
    *,
    edition_date: date | str | None = None,
    force: bool = False,
) -> dict[str, object]:
    """Email Tom if today's edition is unpublished. Never publishes."""
    settings.ensure_dirs()
    store = EditionStore(settings)
    if isinstance(edition_date, str):
        day = edition_date
    elif edition_date is None:
        day = today_melbourne().isoformat()
    else:
        day = edition_date.isoformat()

    if store.is_published(day):
        log.info("Edition %s is already published. No reminder.", day)
        return {"sent": False, "reason": "already_published", "edition_date": day}

    marker = store.reminder_marker(day)
    if marker.is_file() and not force:
        log.info("Reminder already sent for %s.", day)
        return {"sent": False, "reason": "already_sent", "edition_date": day}

    draft = store.load_draft(day)
    from egnooz.emailer import send_reminder

    sent = send_reminder(settings, day, draft)
    if sent:
        store.mark_reminder_sent(day)
    elif not settings.email_ready():
        log.warning(
            "Reminder not sent (email not configured). Draft exists=%s",
            draft is not None,
        )
    return {
        "sent": sent,
        "reason": "unpublished",
        "edition_date": day,
        "draft": draft is not None,
    }
