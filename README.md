# EGNooz

Daily East Gippsland news edition: outbound links with a preview card (title, source, time, short snippet). Tom checks a draft on his phone, then taps **Publish**. Nothing public and no subscriber email goes out without that tap.

This repository is the ingest + review/publish prototype. The Android app comes later and will read `latest.json`. Do not treat ABC’s retired RSS feeds or Google News as inputs.

- **VPS:** `krystalbbs.net`
- **Deploy user:** `krystalbbs`
- **Timezone:** `Australia/Melbourne`
- **Public JSON (after Publish):** `https://krystalbbs.net/editions/latest.json`

No SSH from this repo’s CI. GitHub Actions is not the ingest runtime.

## What runs each Melbourne day

| Time | What happens |
| --- | --- |
| 5:00 am | `egnooz ingest` pulls allowlisted feeds, writes a **draft** JSON, optionally emails Tom “draft ready”. |
| When you have five minutes | Open `https://krystalbbs.net/`, uncheck junk, add a URL if needed, optional editor note, tap **Publish**. |
| Publish | Writes `published/YYYY-MM-DD.json` and `published/latest.json`, then emails the prototype list (Tom only unless you add testers). |
| 10:00 am | `egnooz remind` emails Tom **only if today is still unpublished**. It never publishes. |
| If you skip Publish | Hold. Yesterday’s `latest.json` stays. No subscriber email. |

Local sources default **on** in review. Mention-matches (Guardian Australia, and later others) default **off**. ABC Gippsland is manual-add only.

## Layout

```
sources.yaml          # Tom-editable source list
places.yaml           # East Gippsland + Sale + Maffra
egnooz/               # Python package (ingest, reminder, review app)
deploy/systemd/       # system units (User=krystalbbs)
deploy/systemd-user/  # lingering user units (preferred)
deploy/cron/          # crontab fallback
deploy/nginx/         # reverse proxy example for krystalbbs.net
docs/edition-schema.md
```

Data on the VPS (not in git):

```
/home/krystalbbs/egnooz-data/drafts/YYYY-MM-DD.json
/home/krystalbbs/egnooz-data/published/YYYY-MM-DD.json
/home/krystalbbs/egnooz-data/published/latest.json
```

## Install on krystalbbs.net as `krystalbbs`

Do this on the VPS. Do not put secrets on the command line or in git.

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git

git clone git@github.com:randers1999/EGNooz.git /home/krystalbbs/egnooz
cd /home/krystalbbs/egnooz

bash deploy/install.sh
```

Edit `/home/krystalbbs/.config/egnooz/egnooz.env` (`chmod 600`):

1. `SECRET_KEY` — `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`
2. `REVIEW_PASSWORD` — phone sign-in for the review page
3. `TOM_EMAIL` — draft-ready, 10:00 am reminder, and the prototype edition email
4. `RESEND_API_KEY` and `RESEND_FROM` — leave empty to run without mail
5. `REVIEW_BASE_URL=https://krystalbbs.net`
6. `SESSION_COOKIE_SECURE=true` once nginx is serving HTTPS
7. `EGNOOZ_BIND=127.0.0.1` and `EGNOOZ_PORT=8080` (nginx talks to localhost)

If `krystalbbs.net` already serves another site, do not replace that vhost. Use a subdomain or a path, and change `REVIEW_BASE_URL` to match. Example nginx snippet: `deploy/nginx/krystalbbs.net.conf`.

Enable the user services (lingering so timers fire after logout):

```bash
loginctl enable-linger krystalbbs
systemctl --user daemon-reload
systemctl --user enable --now egnooz-review.service
systemctl --user enable --now egnooz-ingest.timer
systemctl --user enable --now egnooz-reminder.timer
systemctl --user status egnooz-review.service
```

Or install the copies in `deploy/systemd/` into `/etc/systemd/system/` (needs sudo once). They run as `User=krystalbbs`.

Cron instead of timers:

```bash
crontab deploy/cron/egnooz.crontab
```

You still need `egnooz serve` running (the review service) if you use cron for ingest/remind only.

Check:

```bash
/home/krystalbbs/egnooz/.venv/bin/egnooz doctor
/home/krystalbbs/egnooz/.venv/bin/egnooz ingest --no-email
```

Open `https://krystalbbs.net/login`, review, Publish. Until you publish, `https://krystalbbs.net/editions/latest.json` is 404 (or still yesterday).

## Commands

```bash
egnooz ingest              # 5:00 am job; writes draft only
egnooz ingest --no-email
egnooz remind              # 10:00 am job; never publishes
egnooz serve               # review/publish app
egnooz doctor
```

Env file search order: `EGNOOZ_ENV_FILE`, then `~/.config/egnooz/egnooz.env`, then `./.env`.

## Sources (feeds first)

See `sources.yaml`. Live probe on 31 October 2026:

| Source | Automatic ingest | Notes |
| --- | --- | --- |
| Bairnsdale Advertiser, Lakes Post, Snowy River Mail | RSS `/feed/` | Worked from this build environment. Weekly, Wednesday. If the VPS is firewalled, do not scrape HTML. |
| BRHS | `https://brhs.com.au/feed/` | Works. Do not use `/news/feed/` (comments). |
| VicEmergency | official GeoJSON | Warnings strip, CC BY 3.0 AU, East Gippsland + Sale/Maffra. |
| Guardian Australia | RSS | Mention-matches, default off in review. |
| ABC Gippsland | **manual** | RSS retired. Paste URLs during review. |
| EGSC, East Gippsland Water, Vic Premier | none | No official feed found. Paste URLs. No listing scrape. |
| The Age, NewsAPI, REG FM, Destination Gippsland | off | Listed for later. |

Place filter: East Gippsland towns plus **Sale** and **Maffra**. Unqualified “Gippsland”, Latrobe Valley, Traralgon, Morwell, rest of Wellington, Phillip Island, South Gippsland stay out unless an in-scope place is also named.

## Email (Resend)

Prototype emails **Tom only**. `SUBSCRIBER_EMAILS` is optional testers, still only after Publish. Double opt-in and unsubscribe before any public list. Never auto-email the edition.

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

Australian English in user-facing copy. No ads.
