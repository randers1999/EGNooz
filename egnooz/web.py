from __future__ import annotations

import logging
import re
import secrets
from collections import defaultdict, deque
from datetime import datetime, timedelta
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from egnooz import EDITOR_NOTE_MAX, __version__
from egnooz.config import Settings, load_settings
from egnooz.edition import NewsItem
from egnooz.http import FetchError, fetch_bytes
from egnooz.ingest import run_ingest
from egnooz.publish import publish_edition
from egnooz.snippet import make_snippet
from egnooz.store import EditionStore
from egnooz.timeutil import format_item_time, format_long_date, isoformat, now_melbourne, today_melbourne
from egnooz.urls import canonical_url, hostname, item_id

log = logging.getLogger("egnooz.web")

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_login_attempts: dict[str, deque[datetime]] = defaultdict(deque)


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.parts.append(data)


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _too_many_logins(ip: str) -> bool:
    window = datetime.now() - timedelta(minutes=15)
    bucket = _login_attempts[ip]
    while bucket and bucket[0] < window:
        bucket.popleft()
    return len(bucket) >= 10


def _record_login_fail(ip: str) -> None:
    _login_attempts[ip].append(datetime.now())


def fetch_page_title(url: str, user_agent: str) -> str | None:
    try:
        _status, payload, content_type = fetch_bytes(
            url,
            user_agent=user_agent,
            timeout=8.0,
            max_bytes=100_000,
            accept="text/html,application/xhtml+xml",
        )
    except FetchError:
        return None
    if "html" not in (content_type or "").lower() and not payload[:200].lstrip().lower().startswith(b"<!doctype") and b"<html" not in payload[:400].lower():
        return None
    try:
        text = payload.decode("utf-8", errors="ignore")
    except Exception:
        return None
    parser = _TitleParser()
    try:
        parser.feed(text)
        title = make_snippet("".join(parser.parts), limit=180)
    except Exception:
        match = _TITLE_RE.search(text)
        title = make_snippet(match.group(1) if match else "", limit=180)
    return title or None


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or load_settings()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key or "dev-only-not-for-vps"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = settings.session_cookie_secure
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    store = EditionStore(settings)

    app.jinja_env.filters["longdate"] = format_long_date
    app.jinja_env.filters["itemtime"] = format_item_time

    def csrf_token() -> str:
        token = session.get("_csrf")
        if not token:
            token = secrets.token_urlsafe(32)
            session["_csrf"] = token
        return token

    def check_csrf() -> None:
        token = session.get("_csrf")
        submitted = request.form.get("csrf_token", "")
        if not token or not submitted or not secrets.compare_digest(token, submitted):
            abort(400, "That form expired. Refresh the page and try again.")

    def logged_in() -> bool:
        return bool(session.get("reviewer"))

    @app.context_processor
    def inject_globals() -> dict[str, Any]:
        return {
            "csrf_token": csrf_token,
            "logged_in": logged_in(),
            "app_version": __version__,
            "today_label": format_long_date(today_melbourne()),
        }

    @app.after_request
    def security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    def require_login():
        if not logged_in():
            return redirect(url_for("login", next=request.path))
        return None

    def load_today_draft():
        day = today_melbourne().isoformat()
        draft = store.load_draft(day)
        published = store.is_published(day)
        return day, draft, published

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if not settings.review_password:
            return render_template(
                "login.html",
                error="REVIEW_PASSWORD is not set on the server. Add it to the env file.",
            ), 503
        error = None
        if request.method == "POST":
            ip = _client_ip()
            if _too_many_logins(ip):
                error = "Too many attempts. Wait 15 minutes and try again."
            else:
                offered = request.form.get("password") or ""
                if secrets.compare_digest(offered, settings.review_password):
                    session["reviewer"] = "tom"
                    session.permanent = True
                    return redirect(request.args.get("next") or url_for("review"))
                _record_login_fail(ip)
                error = "That password did not match."
        return render_template("login.html", error=error)

    @app.route("/logout", methods=["POST"])
    def logout():
        check_csrf()
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    def review():
        gate = require_login()
        if gate:
            return gate
        day, draft, published = load_today_draft()
        latest = store.load_latest()
        local_items = [i for i in (draft.items if draft else []) if i.match_reason == "local-source"]
        mention_items = [i for i in (draft.items if draft else []) if i.match_reason == "mention"]
        manual_items = [i for i in (draft.items if draft else []) if i.match_reason == "manual"]
        from egnooz.sources import load_sources

        source_choices = [
            s for s in load_sources(settings.sources_path).sources if s.enabled
        ]
        return render_template(
            "review.html",
            day=day,
            draft=draft,
            published=published,
            latest=latest,
            local_items=local_items,
            mention_items=mention_items,
            manual_items=manual_items,
            source_choices=source_choices,
            editor_note_max=EDITOR_NOTE_MAX,
        )

    def _apply_form(draft):
        included_ids = set(request.form.getlist("included"))
        for item in draft.items:
            item.included = item.id in included_ids
        draft.set_editor_note(request.form.get("editor_note") or "")
        return draft

    @app.route("/save", methods=["POST"])
    def save():
        gate = require_login()
        if gate:
            return gate
        check_csrf()
        day, draft, _published = load_today_draft()
        if draft is None:
            flash("No draft to save. Run ingest first.")
            return redirect(url_for("review"))
        store.save_draft(_apply_form(draft))
        if request.headers.get("X-Requested-With") == "fetch":
            return {"ok": True, "savedAt": isoformat(now_melbourne())}
        flash("Draft saved. Nothing has been published.")
        return redirect(url_for("review"))

    @app.route("/add", methods=["POST"])
    def add_url():
        gate = require_login()
        if gate:
            return gate
        check_csrf()
        day, draft, _published = load_today_draft()
        if draft is None:
            flash("No draft yet. Run ingest first, then add the URL.")
            return redirect(url_for("review"))
        url = canonical_url(request.form.get("url") or "")
        if not url or urlparse(url).scheme not in {"http", "https"}:
            flash("Paste a full http(s) URL.")
            return redirect(url_for("review"))
        title = (request.form.get("title") or "").strip()
        source_id = (request.form.get("source_id") or "manual").strip() or "manual"
        source_name = (request.form.get("source_name") or "").strip()
        from egnooz.sources import load_sources

        sources = load_sources(settings.sources_path)
        chosen = sources.by_id(source_id)
        if not source_name:
            source_name = chosen.name if chosen else "Added by Tom"
        if not title:
            title = fetch_page_title(url, sources.user_agent) or hostname(url)
        ident = item_id("manual", url)
        if any(canonical_url(item.url) == url for item in draft.items):
            flash("That URL is already in the draft.")
            return redirect(url_for("review"))
        draft.items.insert(
            0,
            NewsItem(
                id=ident,
                title=make_snippet(title, limit=180),
                url=url,
                source_id=source_id if source_id != "manual" else "manual",
                source_name=source_name,
                published_at=isoformat(now_melbourne()),
                snippet="",
                match_reason="manual",
                matched_places=[],
                included=True,
            ),
        )
        store.save_draft(draft)
        flash("Added to today’s draft. It is ticked on, and still not public until Publish.")
        return redirect(url_for("review"))

    @app.route("/publish", methods=["POST"])
    def publish():
        gate = require_login()
        if gate:
            return gate
        check_csrf()
        day, draft, _published = load_today_draft()
        if draft is None:
            flash("No draft to publish. Run ingest first.")
            return redirect(url_for("review"))
        publish_edition(settings, _apply_form(draft), send_email=True)
        flash("Published. latest.json is updated. Subscriber email only goes out after this tap.")
        return redirect(url_for("review"))

    @app.route("/ingest", methods=["POST"])
    def ingest_now():
        gate = require_login()
        if gate:
            return gate
        check_csrf()
        run_ingest(settings, send_email=False, polite_delay=0.2)
        flash("Ingest finished. Review the draft, then Publish when you are ready.")
        return redirect(url_for("review"))

    @app.route("/editions/latest.json")
    def latest_json():
        latest = store.load_latest()
        if latest is None:
            abort(404)
        return latest.to_public_dict()

    @app.route("/editions/<edition_date>.json")
    def dated_json(edition_date: str):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", edition_date):
            abort(404)
        published = store.load_published(edition_date)
        if published is None:
            abort(404)
        return published.to_public_dict()

    @app.route("/latest")
    def public_latest():
        latest = store.load_latest()
        return render_template("public.html", edition=latest)

    @app.route("/healthz")
    def healthz():
        return {"ok": True, "version": __version__, "timezone": settings.timezone}

    return app


app = None


def __getattr__(name: str):
    global app
    if name == "app":
        if app is None:
            app = create_app()
        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
