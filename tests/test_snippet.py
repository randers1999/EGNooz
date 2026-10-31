from egnooz.snippet import make_snippet, strip_html


def test_strips_html_and_truncates():
    html = "<p>Bairnsdale SES volunteers responded to more than 75 requests for help.</p>"
    assert "Bairnsdale SES" in strip_html(html)
    assert "<p>" not in strip_html(html)
    long = "word " * 80
    snippet = make_snippet(long, limit=40)
    assert len(snippet) <= 41
    assert snippet.endswith("…")


def test_does_not_keep_read_more():
    text = make_snippet("Council meets tonight. Read more")
    assert "Read more" not in text
