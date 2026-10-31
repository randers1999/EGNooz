from __future__ import annotations

import argparse
import json
import logging
import sys

from egnooz import TIMEZONE_NAME, __version__
from egnooz.config import load_settings
from egnooz.timeutil import today_melbourne


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def cmd_ingest(args: argparse.Namespace) -> int:
    from egnooz.ingest import run_ingest

    settings = load_settings()
    edition = run_ingest(
        settings,
        edition_date=args.date,
        send_email=not args.no_email,
    )
    counts = edition.counts()
    print(
        f"Draft {edition.edition_date}: {counts['total']} items "
        f"({counts['local']} local, {counts['mention']} mention, {counts['manual']} manual), "
        f"{counts['warnings']} warnings. Included by default: {counts['included']}."
    )
    failed = [entry for entry in edition.ingest_log if entry.status == "error"]
    for entry in edition.ingest_log:
        extra = entry.error or entry.detail or ""
        print(f"  {entry.source_id}: {entry.status} items={entry.item_count} {extra}".rstrip())
    return 1 if failed else 0


def cmd_remind(args: argparse.Namespace) -> int:
    from egnooz.reminder import run_reminder

    settings = load_settings()
    result = run_reminder(settings, edition_date=args.date, force=args.force)
    print(json.dumps(result, indent=2))
    return 0


def cmd_serve(_args: argparse.Namespace) -> int:
    from waitress import serve

    from egnooz.web import create_app

    settings = load_settings()
    missing = settings.missing_for_serve()
    if missing:
        print(
            "Missing " + ", ".join(missing) + " in the env file. "
            "Copy .env.example to ~/.config/egnooz/egnooz.env on krystalbbs.net.",
            file=sys.stderr,
        )
        return 2
    settings.ensure_dirs()
    app = create_app(settings)
    print(
        f"EGNooz review listening on {settings.bind}:{settings.port} "
        f"(public URL {settings.review_base_url})"
    )
    serve(app, host=settings.bind, port=settings.port, threads=4, ident="egnooz")
    return 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    settings = load_settings()
    print(f"EGNooz {__version__}")
    print(f"timezone: {settings.timezone} (locked {TIMEZONE_NAME})")
    print(f"repo:     {settings.repo_root}")
    print(f"data:     {settings.data_dir}")
    print(f"env file: {settings.env_file or '(none found)'}")
    print(f"host URL: {settings.review_base_url}")
    print(f"bind:     {settings.bind}:{settings.port}")
    print(f"today:    {today_melbourne().isoformat()}")
    print(f"SECRET_KEY set: {'yes' if settings.secret_key else 'NO'}")
    print(f"REVIEW_PASSWORD set: {'yes' if settings.review_password else 'NO'}")
    print(f"TOM_EMAIL set: {'yes' if settings.tom_email else 'NO'}")
    print(f"RESEND_API_KEY set: {'yes' if settings.resend_api_key else 'NO'}")
    print(f"RESEND_FROM set: {'yes' if settings.resend_from else 'NO'}")
    print(f"sources.yaml: {'ok' if settings.sources_path.is_file() else 'MISSING'}")
    print(f"places.yaml:  {'ok' if settings.places_path.is_file() else 'MISSING'}")
    settings.ensure_dirs()
    print("data dirs: ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="egnooz",
        description="EGNooz ingest, reminder, and review server for krystalbbs.net",
    )
    parser.add_argument("--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Pull feeds and write today's draft JSON")
    ingest.add_argument("--date", help="YYYY-MM-DD (defaults to today in Melbourne)")
    ingest.add_argument("--no-email", action="store_true", help="Do not send draft-ready email")
    ingest.set_defaults(func=cmd_ingest)

    remind = sub.add_parser("remind", help="Email Tom if today's edition is unpublished")
    remind.add_argument("--date", help="YYYY-MM-DD (defaults to today in Melbourne)")
    remind.add_argument("--force", action="store_true", help="Send even if already reminded today")
    remind.set_defaults(func=cmd_remind)

    serve_p = sub.add_parser("serve", help="Run the review/publish web app")
    serve_p.set_defaults(func=cmd_serve)

    doctor = sub.add_parser("doctor", help="Check paths and env on this VPS")
    doctor.set_defaults(func=cmd_doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)
    return args.func(args)
