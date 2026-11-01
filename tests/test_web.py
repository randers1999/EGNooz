from __future__ import annotations

from pathlib import Path

from egnooz.edition import Edition, NewsItem
from egnooz.store import EditionStore
from egnooz.timeutil import today_melbourne
from egnooz.web import create_app

RSS = Path(__file__).resolve().parent / "fixtures" / "sample.rss.xml"
VIC = Path(__file__).resolve().parent / "fixtures" / "vicemergency.json"


def _client(settings):
    app = create_app(settings)
    app.config["TESTING"] = True
    return app.test_client()


def _login(client):
    return client.post("/login", data={"password": "test-pass"}, follow_redirects=True)


def _csrf(client):
    with client.session_transaction() as sess:
        return sess["_csrf"]


def test_latest_json_404_until_publish(settings, monkeypatch):
    monkeypatch.setattr("egnooz.emailer.send_edition", lambda *a, **k: True)
    client = _client(settings)
    assert client.get("/editions/latest.json").status_code == 404
    _login(client)
    store = EditionStore(settings)
    store.save_draft(
        Edition(
            edition_date=today_melbourne().isoformat(),
            items=[
                NewsItem(
                    id="keep",
                    title="Bairnsdale item",
                    url="https://example.test/a",
                    source_id="brhs",
                    source_name="BRHS",
                    published_at=None,
                    snippet="Snippet",
                    match_reason="local-source",
                    included=True,
                ),
                NewsItem(
                    id="drop",
                    title="Mention item",
                    url="https://example.test/b",
                    source_id="guardian-au",
                    source_name="Guardian Australia",
                    published_at=None,
                    snippet="Sale mention",
                    match_reason="mention",
                    included=False,
                ),
            ],
        )
    )
    page = client.get("/")
    assert page.status_code == 200
    assert b"Local sources" in page.data
    assert b"Mentions East Gippsland" in page.data
    assert b"default off" in page.data
    csrf = _csrf(client)
    published = client.post(
        "/publish",
        data={"csrf_token": csrf, "included": "keep", "editor_note": "Quiet news day."},
        follow_redirects=True,
    )
    assert published.status_code == 200
    latest = client.get("/editions/latest.json")
    assert latest.status_code == 200
    body = latest.get_json()
    assert body["status"] == "published"
    assert body["editorNote"] == "Quiet news day."
    assert [item["title"] for item in body["items"]] == ["Bairnsdale item"]
    assert "ingestLog" not in body


def test_review_requires_password(settings):
    client = _client(settings)
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_add_url_and_uncheck(settings, monkeypatch):
    monkeypatch.setattr("egnooz.web.fetch_page_title", lambda url, ua: "ABC Gippsland hand add")
    from egnooz.timeutil import today_melbourne

    store = EditionStore(settings)
    day = today_melbourne().isoformat()
    store.save_draft(Edition(edition_date=day))
    client = _client(settings)
    _login(client)
    csrf = _csrf(client)
    client.post(
        "/add",
        data={
            "csrf_token": csrf,
            "url": "https://www.abc.net.au/news/east-gippsland-example",
            "source_id": "abc-gippsland",
        },
        follow_redirects=True,
    )
    draft = store.load_draft(day)
    assert draft is not None
    assert draft.items[0].match_reason == "manual"
    assert draft.items[0].included is True
    assert draft.items[0].source_name == "ABC Gippsland"
