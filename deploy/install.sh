#!/usr/bin/env bash
# Run on krystalbbs.net as user egnooz (home /home/egnooz).
# Tom may log in as tom to create that user. This script does not SSH and does not print secrets.
set -euo pipefail

HOST_USER="egnooz"
ROOT="${EGNOOZ_ROOT:-/home/${HOST_USER}/egnooz}"
DATA="${EGNOOZ_DATA_DIR:-/home/${HOST_USER}/egnooz-data}"
ENV_DIR="/home/${HOST_USER}/.config/egnooz"
ENV_FILE="${ENV_DIR}/egnooz.env"
UNIT_DIR="/home/${HOST_USER}/.config/systemd/user"

if [[ "$(id -un)" != "${HOST_USER}" ]]; then
  echo "Run this as ${HOST_USER} on krystalbbs.net (now: $(id -un))." >&2
  exit 1
fi

if [[ ! -f "${ROOT}/pyproject.toml" ]]; then
  echo "Clone the repo to ${ROOT} first." >&2
  exit 1
fi

mkdir -p "${DATA}/drafts" "${DATA}/published" "${DATA}/state" "${ENV_DIR}" "${UNIT_DIR}"
chmod 700 "${DATA}" "${ENV_DIR}"

if [[ ! -d "${ROOT}/.venv" ]]; then
  python3 -m venv "${ROOT}/.venv"
fi
"${ROOT}/.venv/bin/pip" install --upgrade pip
"${ROOT}/.venv/bin/pip" install -e "${ROOT}"

if [[ ! -f "${ENV_FILE}" ]]; then
  cp "${ROOT}/.env.example" "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
  echo "Wrote ${ENV_FILE} from .env.example. Fill SECRET_KEY, REVIEW_PASSWORD, TOM_EMAIL, Resend keys. Never commit that file."
else
  chmod 600 "${ENV_FILE}"
  echo "Keeping existing ${ENV_FILE}"
fi

cp "${ROOT}/deploy/systemd-user/"* "${UNIT_DIR}/"

# System-level copies keep User=egnooz for /etc/systemd/system if you prefer a root install.
echo
echo "Next on krystalbbs.net (as user egnooz):"
echo "  1. Edit ${ENV_FILE} (chmod 600). Generate SECRET_KEY; set REVIEW_PASSWORD and TOM_EMAIL."
echo "  2. If linger is not on yet, as tom: sudo loginctl enable-linger ${HOST_USER}"
echo "  3. systemctl --user daemon-reload"
echo "  4. systemctl --user enable --now egnooz-review.service egnooz-ingest.timer egnooz-reminder.timer"
echo "  5. Point nginx on https://krystalbbs.net at 127.0.0.1:8080 (see deploy/nginx/krystalbbs.net.conf)"
echo "  6. ${ROOT}/.venv/bin/egnooz doctor"
echo "  7. ${ROOT}/.venv/bin/egnooz ingest --no-email"
echo
echo "Do not put the Resend key or review password on a command line."
echo "Cron alternative: crontab deploy/cron/egnooz.crontab"
echo "Systemd system units (need sudo once): copy deploy/systemd/*.service and *.timer to /etc/systemd/system/"
