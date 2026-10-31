from __future__ import annotations

import logging
from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape

from egnooz.config import Settings
from egnooz.edition import Edition
from egnooz.timeutil import format_item_time, format_long_date

log = logging.getLogger("egnooz.emailer")

RESEND_URL = "https://api.resend.com/emails"


def _templates() -> Environment:
    folder = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(folder)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["longdate"] = format_long_date
    env.filters["itemtime"] = format_item_time
    return env


def _html(name: str, **context: object) -> str:
    return _templates().get_template(name).render(**context)


def send_resend_email(
    settings: Settings,
    *,
    to: list[str],
    subject: str,
    html: str,
) -> bool:
    if not settings.resend_api_key:
        log.warning("Email skipped: RESEND_API_KEY is not set")
        return False
    if not settings.resend_from:
        log.warning("Email skipped: RESEND_FROM is not set")
        return False
    recipients = [addr for addr in to if addr]
    if not recipients:
        log.warning("Email skipped: no recipients")
        return False
    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": settings.resend_from,
        "to": recipients,
        "subject": subject,
        "html": html,
    }
    try:
        response = httpx.post(RESEND_URL, json=payload, headers=headers, timeout=20.0)
    except httpx.HTTPError as exc:
        log.error("Resend request failed: %s", exc)
        return False
    if response.status_code >= 400:
        log.error("Resend HTTP %s", response.status_code)
        return False
    log.info("Sent email via Resend to %s recipients", len(recipients))
    return True


def send_draft_ready(settings: Settings, edition: Edition) -> bool:
    if not settings.tom_email:
        log.warning("Draft-ready email skipped: TOM_EMAIL is not set")
        return False
    counts = edition.counts()
    subject = (
        f"EGNooz draft ready — {counts['total']} items. Review."
    )
    html = _html(
        "email_draft.html",
        edition=edition,
        counts=counts,
        review_url=settings.review_url("/"),
        date_label=format_long_date(edition.edition_date),
    )
    return send_resend_email(
        settings, to=[settings.tom_email], subject=subject, html=html
    )


def send_reminder(settings: Settings, edition_date: str, draft: Edition | None) -> bool:
    if not settings.tom_email:
        log.warning("Reminder skipped: TOM_EMAIL is not set")
        return False
    counts = draft.counts() if draft else {"total": 0, "included": 0, "warnings": 0}
    subject = "EGNooz — today's edition is not published yet"
    html = _html(
        "email_reminder.html",
        edition=draft,
        counts=counts,
        review_url=settings.review_url("/"),
        date_label=format_long_date(edition_date),
        edition_date=edition_date,
    )
    return send_resend_email(
        settings, to=[settings.tom_email], subject=subject, html=html
    )


def send_edition(settings: Settings, edition: Edition) -> bool:
    recipients = [settings.tom_email] if settings.tom_email else []
    recipients.extend(addr for addr in settings.subscriber_emails if addr not in recipients)
    if not recipients:
        log.warning("Edition email skipped: no TOM_EMAIL or SUBSCRIBER_EMAILS")
        return False
    date_label = format_long_date(edition.edition_date)
    subject = f"EGNooz — {date_label}"
    html = _html(
        "email_edition.html",
        edition=edition,
        items=edition.included_items(),
        date_label=date_label,
        latest_url=settings.review_url("/editions/latest.json"),
        public_url=settings.review_url("/latest"),
    )
    return send_resend_email(settings, to=recipients, subject=subject, html=html)
