#!/usr/bin/env bash
# Clone or re-point the private EGNooz repo as user egnooz using a read-only
# GitHub deploy key over SSH. Never uses HTTPS. Never prompts for a password.
set -euo pipefail

HOST_USER="egnooz"
DEST="${EGNOOZ_ROOT:-/home/${HOST_USER}/egnooz}"
REPO_SSH="git@github.com:randers1999/EGNooz.git"
KEY="${HOME}/.ssh/egnooz_github"

export GIT_TERMINAL_PROMPT=0
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0="credential.helper"
export GIT_CONFIG_VALUE_0=""

if [[ "$(id -un)" != "${HOST_USER}" ]]; then
  echo "Run this as ${HOST_USER} on krystalbbs.net (now: $(id -un))." >&2
  exit 1
fi

mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"

if [[ ! -f "${KEY}" ]]; then
  ssh-keygen -t ed25519 -f "${KEY}" -N "" -C "egnooz@krystalbbs.net deploy (read-only)"
  chmod 600 "${KEY}" "${KEY}.pub"
  echo "Created ${KEY} with an empty passphrase so git never asks."
  echo
  echo "Add the public key as a read-only deploy key in the GitHub website"
  echo "(randers1999/EGNooz → Settings → Deploy keys → Add deploy key)."
  echo "Title: krystalbbs.net egnooz. Leave write access off."
  echo "Do not paste the private key anywhere. Do not paste credentials into chat."
  echo
  echo "Public key (safe to paste into GitHub Deploy keys):"
  cat "${KEY}.pub"
  echo
  echo "Then run: $0"
  exit 2
fi

chmod 600 "${KEY}"
chmod 644 "${KEY}.pub"

SSH_CONFIG="${HOME}/.ssh/config"
if [[ ! -f "${SSH_CONFIG}" ]] || ! grep -q "IdentityFile ${KEY}" "${SSH_CONFIG}"; then
  {
    echo ""
    echo "Host github.com"
    echo "  HostName github.com"
    echo "  User git"
    echo "  IdentityFile ${KEY}"
    echo "  IdentitiesOnly yes"
    echo "  BatchMode yes"
    echo "  PreferredAuthentications publickey"
  } >> "${SSH_CONFIG}"
  chmod 600 "${SSH_CONFIG}"
fi

KNOWN="${HOME}/.ssh/known_hosts"
touch "${KNOWN}"
chmod 600 "${KNOWN}"
if ! ssh-keygen -F github.com -f "${KNOWN}" >/dev/null 2>&1; then
  ssh-keyscan -t ed25519 github.com >> "${KNOWN}" 2>/dev/null
fi

set +e
ssh_out="$(ssh -o BatchMode=yes -o PreferredAuthentications=publickey -o StrictHostKeyChecking=yes -T git@github.com 2>&1)"
set -e
if ! grep -qi "successfully authenticated" <<<"${ssh_out}"; then
  echo "GitHub SSH failed without asking for a password. Add the public key as a" >&2
  echo "read-only deploy key, then retry. Public key:" >&2
  cat "${KEY}.pub" >&2
  echo "${ssh_out}" >&2
  exit 2
fi

if [[ -d "${DEST}/.git" ]]; then
  origin="$(git -C "${DEST}" remote get-url origin 2>/dev/null || true)"
  if [[ "${origin}" == https://* ]]; then
    echo "origin is HTTPS, which hangs on this private repo with no TTY."
    git -C "${DEST}" remote set-url origin "${REPO_SSH}"
    echo "Switched origin to ${REPO_SSH}"
  fi
  echo "Repo already at ${DEST}"
  git -C "${DEST}" remote -v
  exit 0
fi

if [[ -e "${DEST}" ]]; then
  echo "${DEST} exists but is not a git checkout. Move it aside, then retry." >&2
  exit 1
fi

git -c credential.helper= clone "${REPO_SSH}" "${DEST}"
echo "Cloned ${REPO_SSH} to ${DEST}"
