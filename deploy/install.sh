#!/usr/bin/env bash
# Run on krystalbbs.net as user egnooz (home /home/egnooz).
# Uses an existing git checkout — including /home/egnooz/EGNooz (GitHub's
# default clone name) and $PWD when this is already the repo. Does not
# require a second clone to /home/egnooz/egnooz.
# Tom may log in as tom to create the user. This script does not SSH and
# does not print secrets. HTTPS and github.com:22 stay refused.
set -euo pipefail

HOST_USER="egnooz"
DATA="${EGNOOZ_DATA_DIR:-/home/${HOST_USER}/egnooz-data}"
ENV_DIR="/home/${HOST_USER}/.config/egnooz"
ENV_FILE="${ENV_DIR}/egnooz.env"
UNIT_DIR="/home/${HOST_USER}/.config/systemd/user"
REPO_SSH="git@github.com:randers1999/EGNooz.git"

if [[ "$(id -un)" != "${HOST_USER}" ]]; then
  echo "Run this as ${HOST_USER} on krystalbbs.net (now: $(id -un))." >&2
  exit 1
fi

is_egnooz_tree() {
  local d="${1:-}"
  [[ -n "${d}" && -d "${d}" && -f "${d}/pyproject.toml" && -d "${d}/egnooz" && -f "${d}/deploy/install.sh" ]]
}

abs_tree() {
  (cd "${1}" && pwd)
}

# Prefer a valid EGNOOZ_ROOT; otherwise any existing checkout. Ignore an
# EGNOOZ_ROOT that points at a missing lowercase path when EGNooz is already here.
ROOT=""
if [[ -n "${EGNOOZ_ROOT:-}" ]] && is_egnooz_tree "${EGNOOZ_ROOT}"; then
  ROOT="$(abs_tree "${EGNOOZ_ROOT}")"
fi
if [[ -z "${ROOT}" ]] && is_egnooz_tree "${PWD}"; then
  ROOT="$(abs_tree "${PWD}")"
fi
if [[ -z "${ROOT}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if is_egnooz_tree "${SCRIPT_DIR}/.."; then
    ROOT="$(abs_tree "${SCRIPT_DIR}/..")"
  fi
fi
if [[ -z "${ROOT}" ]] && is_egnooz_tree "/home/${HOST_USER}/EGNooz"; then
  ROOT="$(abs_tree "/home/${HOST_USER}/EGNooz")"
fi
if [[ -z "${ROOT}" ]] && is_egnooz_tree "/home/${HOST_USER}/egnooz"; then
  ROOT="$(abs_tree "/home/${HOST_USER}/egnooz")"
fi

if [[ -z "${ROOT}" ]]; then
  echo "No EGNooz git checkout found. Clone once over SSH, then run this script from that tree." >&2
  echo "GitHub's default directory is /home/${HOST_USER}/EGNooz — that is fine. Do not clone a second copy into /home/${HOST_USER}/egnooz." >&2
  echo "HTTPS hangs; github.com:22 times out. Use ssh.github.com port 443." >&2
  echo "As ${HOST_USER}:" >&2
  echo "  export GIT_TERMINAL_PROMPT=0" >&2
  echo "  export GIT_SSH_COMMAND=\"ssh -i \${HOME}/.ssh/egnooz_github -p 443 -o HostName=ssh.github.com -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o BatchMode=yes\"" >&2
  echo "  git -c credential.helper= clone ${REPO_SSH}" >&2
  echo "  cd EGNooz && bash deploy/install.sh" >&2
  echo "Never HTTPS or port 22." >&2
  exit 1
fi

echo "Using existing checkout ${ROOT} (no second clone)."

if [[ -d "${ROOT}/.git" ]]; then
  origin="$(git -C "${ROOT}" remote get-url origin 2>/dev/null || true)"
  if [[ "${origin}" == https://* || "${origin}" == http://* ]]; then
    echo "origin is HTTPS (${origin}). That hangs on this private repo with no TTY." >&2
    echo "Switch to SSH, then retry:" >&2
    echo "  git -C ${ROOT} remote set-url origin ${REPO_SSH}" >&2
    echo "Or run: bash ${ROOT}/deploy/clone.sh" >&2
    exit 1
  fi
fi

rewrite_repo_paths() {
  # Rewrite checkout paths only. Do not touch /home/egnooz/egnooz-data
  # or /home/egnooz/.config/egnooz (those are not the git tree).
  sed \
    -e "s#/home/${HOST_USER}/EGNooz#${ROOT}#g" \
    -e "s#/home/${HOST_USER}/egnooz/#${ROOT}/#g" \
    -e "s#cd /home/${HOST_USER}/egnooz #cd ${ROOT} #g" \
    -e "s#EGNOOZ_ROOT=/home/${HOST_USER}/egnooz\$#EGNOOZ_ROOT=${ROOT}#" \
    -e "s#WorkingDirectory=/home/${HOST_USER}/egnooz\$#WorkingDirectory=${ROOT}#"
}

mkdir -p "${DATA}/drafts" "${DATA}/published" "${DATA}/state" "${ENV_DIR}" "${UNIT_DIR}"
chmod 700 "${DATA}" "${ENV_DIR}"

if [[ ! -d "${ROOT}/.venv" ]]; then
  python3 -m venv "${ROOT}/.venv"
fi
"${ROOT}/.venv/bin/pip" install --upgrade pip
"${ROOT}/.venv/bin/pip" install -e "${ROOT}"

if [[ ! -f "${ENV_FILE}" ]]; then
  rewrite_repo_paths < "${ROOT}/.env.example" > "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
  echo "Wrote ${ENV_FILE} from .env.example. Fill SECRET_KEY, REVIEW_PASSWORD, TOM_EMAIL, Resend keys. Never commit that file."
else
  chmod 600 "${ENV_FILE}"
  echo "Keeping existing ${ENV_FILE}"
fi
if grep -q '^EGNOOZ_ROOT=' "${ENV_FILE}"; then
  sed -i "s|^EGNOOZ_ROOT=.*|EGNOOZ_ROOT=${ROOT}|" "${ENV_FILE}"
else
  printf '\nEGNOOZ_ROOT=%s\n' "${ROOT}" >> "${ENV_FILE}"
fi
chmod 600 "${ENV_FILE}"

for src in "${ROOT}/deploy/systemd-user/"*; do
  dest="${UNIT_DIR}/$(basename "${src}")"
  rewrite_repo_paths < "${src}" > "${dest}"
done

rewrite_repo_paths < "${ROOT}/deploy/cron/egnooz.crontab" > "${ENV_DIR}/egnooz.crontab"

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
echo "Cron alternative: crontab ${ENV_DIR}/egnooz.crontab"
echo "Systemd system units (need sudo once): copy deploy/systemd/*.service and *.timer to /etc/systemd/system/"
echo "  (edit WorkingDirectory / ExecStart / EGNOOZ_ROOT to ${ROOT} if you copy those by hand)."
