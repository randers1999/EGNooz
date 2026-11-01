# EGNooz

Daily East Gippsland news edition: outbound links with a preview card (title, source, time, short snippet). Tom checks a draft on his phone, then taps **Publish**. Nothing public and no subscriber email goes out without that tap.

This repository is the ingest + review/publish prototype. The Android app comes later and will read `latest.json`. Do not treat ABC’s retired RSS feeds or Google News as inputs.

- **VPS:** `krystalbbs.net` (apex already serves another site — leave that vhost alone)
- **App host:** `egnooz.krystalbbs.net` (subdomain on the same box; rename in nginx + `REVIEW_BASE_URL`)
- **App user:** `egnooz` (home `/home/egnooz`). Tom may log in as `tom` to create that user.
- **Timezone:** `Australia/Melbourne`
- **Public JSON (after Publish):** `https://egnooz.krystalbbs.net/editions/latest.json`

No SSH from this repo’s CI. GitHub Actions is not the ingest runtime.

## What runs each Melbourne day

| Time | What happens |
| --- | --- |
| 5:00 am | `egnooz ingest` pulls allowlisted feeds, writes a **draft** JSON, optionally emails Tom “draft ready”. |
| When you have five minutes | Open `https://egnooz.krystalbbs.net/`, uncheck junk, add a URL if needed, optional editor note, tap **Publish**. |
| Publish | Writes `published/YYYY-MM-DD.json` and `published/latest.json`, then emails the prototype list (Tom only unless you add testers). |
| 10:00 am | `egnooz remind` emails Tom **only if today is still unpublished**. It never publishes. |
| If you skip Publish | Hold. Yesterday’s `latest.json` stays. No subscriber email. |

Local sources default **on** in review. Mention-matches (Guardian Australia, and later others) default **off**. ABC Gippsland is manual-add only.

## Layout

```
sources.yaml          # Tom-editable source list
places.yaml           # East Gippsland + Sale + Maffra
egnooz/               # Python package (ingest, reminder, review app)
deploy/systemd/       # system units (User=egnooz)
deploy/systemd-user/  # lingering user units (preferred)
deploy/clone.sh       # SSH deploy-key clone (no HTTPS, no password prompt)
deploy/cron/          # crontab fallback
deploy/nginx/         # subdomain vhost (egnooz.krystalbbs.net); do not replace the apex site
docs/edition-schema.md
```

Data on the VPS (not in git):

```
/home/egnooz/egnooz-data/drafts/YYYY-MM-DD.json
/home/egnooz/egnooz-data/published/YYYY-MM-DD.json
/home/egnooz/egnooz-data/published/latest.json
```

## Install on krystalbbs.net as `egnooz`

Do this on the VPS. Do not put secrets on the command line or in git.

You can still log in as `tom` to create the dedicated app user, then run the app as `egnooz` (home `/home/egnooz`):

```bash
# as tom, once
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git openssh-client
sudo useradd --create-home --home-dir /home/egnooz --shell /bin/bash egnooz
sudo loginctl enable-linger egnooz
sudo -iu egnooz
```

### Clone the private repo (read-only SSH deploy key)

This repo is **private**. HTTPS clone hangs with no TTY. On krystalbbs.net, **`github.com:22` times out** — use GitHub’s SSH-over-443 endpoint instead. Do not scan or connect to port 22. Do not paste credentials into chat.

Key file: **`~/.ssh/egnooz_github`** (and `egnooz_github.pub`). `deploykey1` is only a fallback. `known_hosts` starts empty — seed **port 443**.

As `egnooz` — non-interactive, no password prompt:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
chmod 600 ~/.ssh/egnooz_github

cat > ~/.ssh/config <<'EOF'
Host github.com
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile ~/.ssh/egnooz_github
  IdentitiesOnly yes
  BatchMode yes
EOF
chmod 600 ~/.ssh/config

# Do not ssh-keyscan github.com (port 22 hangs). Use 443:
ssh-keyscan -p 443 -t ed25519 ssh.github.com >> ~/.ssh/known_hosts 2>/dev/null

echo "Add this public key as a read-only deploy key:"
echo "GitHub → randers1999/EGNooz → Settings → Deploy keys → Add deploy key"
echo "Title: krystalbbs.net egnooz. Leave write access off."
cat ~/.ssh/egnooz_github.pub
```

On your own computer (as GitHub user `randers1999`), add that **public** key as a deploy key. Do not enable write access. Do not copy the private key off the VPS.

Then as `egnooz` (SSH over 443; refuses HTTPS; no prompts):

```bash
# If a hung clone left a half-written directory:
# mv /home/egnooz/EGNooz /home/egnooz/EGNooz.stalled

export GIT_TERMINAL_PROMPT=0
export GIT_SSH_COMMAND="ssh -i ${HOME}/.ssh/egnooz_github -p 443 -o HostName=ssh.github.com -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o BatchMode=yes"
# GitHub's default directory is EGNooz. That is the checkout — do not clone again into ~/egnooz.
git -c credential.helper= clone git@github.com:randers1999/EGNooz.git
cd ~/EGNooz
bash deploy/install.sh
```

If the tree is already at `/home/egnooz/EGNooz` (or you are standing in this repo), run `bash deploy/install.sh` from there. It treats that checkout as success and does **not** require a second clone to `/home/egnooz/egnooz`. `deploy/clone.sh` does the same.

`deploy/clone.sh` writes that `Host github.com` block, runs `ssh-keyscan -p 443 ssh.github.com`, sets the same `GIT_SSH_COMMAND`, prefers `~/.ssh/egnooz_github`, and refuses HTTPS.

Edit `/home/egnooz/.config/egnooz/egnooz.env` (`chmod 600`):

1. `SECRET_KEY` — `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`
2. `REVIEW_PASSWORD` — phone sign-in for the review page
3. `TOM_EMAIL` — draft-ready, 10:00 am reminder, and the prototype edition email
4. `RESEND_API_KEY` and `RESEND_FROM` — leave empty to run without mail
5. `REVIEW_BASE_URL=https://egnooz.krystalbbs.net` (must match the nginx `server_name` if you rename the subdomain)
6. `SESSION_COOKIE_SECURE=true` once certbot is serving HTTPS
7. `EGNOOZ_BIND=127.0.0.1` and `EGNOOZ_PORT=8080` (nginx talks to localhost)

`deploy/install.sh` **never overwrites** `~/.config/egnooz/egnooz.env` (creates it from `.env.example` only if missing). It prints a warning if the clone has a repo-root `.env` and will not touch that file either.

`deploy/install.sh` **always overwrites** `~/.config/systemd/user/*.service` and `*.timer` from `deploy/systemd-user/` (git pull alone does not). After every pull, run `bash deploy/install.sh` as `egnooz`.

### Subdomain nginx (do not replace krystalbbs.net)

The apex `krystalbbs.net` vhost stays. EGNooz is an extra site on the same box.

**DNS** (same addresses as `krystalbbs.net`):

```
egnooz.krystalbbs.net.   A      <IPv4 of krystalbbs.net>
egnooz.krystalbbs.net.   AAAA   <IPv6 of krystalbbs.net, if any>
```

Or `CNAME egnooz.krystalbbs.net. → krystalbbs.net.` To use another name, change `server_name` in `deploy/nginx/egnooz.krystalbbs.net.conf` and `REVIEW_BASE_URL` together.

**Enable + TLS** (as root; leaves the existing vhost alone):

```bash
sudo cp /home/egnooz/EGNooz/deploy/nginx/egnooz.krystalbbs.net.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/egnooz.krystalbbs.net.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d egnooz.krystalbbs.net
```

The snippet is HTTP-only so `nginx -t` works before certificates exist. `certbot --nginx` adds listen 443 and the Let’s Encrypt files. After TLS, keep `SESSION_COOKIE_SECURE=true` and `REVIEW_BASE_URL=https://egnooz.krystalbbs.net`.

Enable the user services (as `egnooz`; linger should already be on from the `tom` step):

```bash
systemctl --user daemon-reload
systemctl --user enable --now egnooz-review.service
systemctl --user enable --now egnooz-ingest.timer
systemctl --user enable --now egnooz-reminder.timer
systemctl --user status egnooz-review.service
systemctl --user list-timers --all
```

Or install the copies in `deploy/systemd/` into `/etc/systemd/system/` (needs sudo once). They run as `User=egnooz`.

Cron instead of timers:

```bash
# install.sh writes a copy with the checkout path filled in:
crontab ~/.config/egnooz/egnooz.crontab
```

You still need `egnooz serve` running (the review service) if you use cron for ingest/remind only.

Check:

```bash
# From the checkout (often /home/egnooz/EGNooz; /home/egnooz/egnooz is also fine):
.venv/bin/egnooz doctor
.venv/bin/egnooz ingest --no-email
```

Open `https://egnooz.krystalbbs.net/login`, review, Publish. Until you publish, `https://egnooz.krystalbbs.net/editions/latest.json` is 404 (or still yesterday).

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
