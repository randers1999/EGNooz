from egnooz.edition import Edition
from egnooz.publish import publish_edition
from egnooz.reminder import run_reminder
from egnooz.store import EditionStore


def test_reminder_skips_when_published(settings, monkeypatch):
    sent = []
    monkeypatch.setattr("egnooz.emailer.send_reminder", lambda *a, **k: sent.append("reminder") or True)
    monkeypatch.setattr("egnooz.emailer.send_edition", lambda *a, **k: True)
    store = EditionStore(settings)
    draft = Edition(edition_date="2026-10-31")
    store.save_draft(draft)
    publish_edition(settings, draft, send_email=False)
    result = run_reminder(settings, edition_date="2026-10-31")
    assert result["reason"] == "already_published"
    assert result["sent"] is False
    assert sent == []


def test_reminder_sends_once_when_unpublished(settings, monkeypatch):
    sent = []
    monkeypatch.setattr("egnooz.emailer.send_reminder", lambda *a, **k: sent.append("reminder") or True)
    store = EditionStore(settings)
    store.save_draft(Edition(edition_date="2026-10-31"))
    first = run_reminder(settings, edition_date="2026-10-31")
    second = run_reminder(settings, edition_date="2026-10-31")
    assert first["sent"] is True
    assert second["reason"] == "already_sent"
    assert sent == ["reminder"]
    assert not store.is_published("2026-10-31")
