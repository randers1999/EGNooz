from egnooz.edition import Edition, NewsItem
from egnooz.publish import publish_edition
from egnooz.store import EditionStore


def test_publish_writes_latest_and_strips_draft_fields(settings, monkeypatch):
    monkeypatch.setattr("egnooz.emailer.send_edition", lambda *args, **kwargs: True)
    edition = Edition(
        edition_date="2026-10-31",
        items=[
            NewsItem(
                id="one",
                title="Keep me",
                url="https://example.test/keep",
                source_id="brhs",
                source_name="BRHS",
                published_at="2026-10-31T08:00:00+11:00",
                snippet="Hospital news in Bairnsdale.",
                match_reason="local-source",
                included=True,
            ),
            NewsItem(
                id="two",
                title="Drop me",
                url="https://example.test/drop",
                source_id="guardian-au",
                source_name="Guardian Australia",
                published_at="2026-10-31T07:00:00+11:00",
                snippet="Mentions Sale.",
                match_reason="mention",
                included=False,
            ),
        ],
    )
    published = publish_edition(settings, edition, send_email=True)
    store = EditionStore(settings)
    assert store.is_published("2026-10-31")
    latest = store.load_latest()
    assert latest is not None
    public = latest.to_public_dict()
    assert public["status"] == "published"
    assert [item["title"] for item in public["items"]] == ["Keep me"]
    assert "included" not in public["items"][0]
    assert "ingestLog" not in public
    assert published.published_at
