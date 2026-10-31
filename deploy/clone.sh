#!/usr/bin/env bash
# Clone the private EGNooz repo as user egnooz over SSH, with no prompts.
# GitHub port 22 times out on krystalbbs.net, so SSH goes via ssh.github.com:443.
# Refuses HTTPS. Prefers ~/.ssh/egnooz_github, then deploykey1.
set -euo pipefail

HOST_USER="egnooz"
DEST="${EGNOOZ_ROOT:-/home/${HOST_USER}/egnooz}"
REPO_SSH="git@github.com:randers1999/EGNooz.git"
SSH_DIR="${HOME}/.ssh"
KNOWN="${SSH_DIR}/known_hosts"
SSH_CONFIG="${SSH_DIR}/config"
BEGIN_MARK="# BEGIN egnooz github ssh"
END_MARK="# END egnooz github ssh"

export GIT_TERMINAL_PROMPT=0
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0="credential.helper"
export GIT_CONFIG_VALUE_0=""

if [[ "$(id -un)" != "${HOST_USER}" ]]; then
  echo "Run this as ${HOST_USER} on krystalbbs.net (now: $(id -un))." >&2
  exit 1
fi

mkdir -p "${SSH_DIR}"
chmod 700 "${SSH_DIR}"

pick_key() {
  local k name
  if [[ -n "${EGNOOZ_SSH_KEY:-}" ]]; then
    k="${EGNOOZ_SSH_KEY}"
    [[ "${k}" == /* ]] || k="${SSH_DIR}/${k}"
    if [[ -f "${k}" ]]; then
      printf '%s\n' "${k}"
      return 0
    fi
    echo "EGNOOZ_SSH_KEY is set but not a file: ${k}" >&2
    exit 1
  fi
  for name in egnooz_github deploykey1 id_ed25519; do
    if [[ -f "${SSH_DIR}/${name}" ]]; then
      printf '%s\n' "${SSH_DIR}/${name}"
      return 0
    fi
  done
  return 1
}

if ! KEY="$(pick_key)"; then
  KEY="${SSH_DIR}/egnooz_github"
  ssh-keygen -t ed25519 -f "${KEY}" -N "" -C "egnooz@krystalbbs.net deploy (read-only)"
  chmod 600 "${KEY}"
  [[ -f "${KEY}.pub" ]] && chmod 644 "${KEY}.pub"
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
[[ -f "${KEY}.pub" ]] && chmod 644 "${KEY}.pub"

echo "Using SSH key ${KEY}"
echo "GitHub SSH via ssh.github.com port 443 (port 22 times out on this VPS)."

# ~/.ssh/config so git@github.com uses 443 without a password prompt.
touch "${SSH_CONFIG}"
chmod 600 "${SSH_CONFIG}"
if grep -q "^${BEGIN_MARK}$" "${SSH_CONFIG}"; then
  awk -v b="${BEGIN_MARK}" -v e="${END_MARK}" '
    $0==b {skip=1; next}
    $0==e {skip=0; next}
    !skip {print}
  ' "${SSH_CONFIG}" > "${SSH_CONFIG}.tmp"
  mv "${SSH_CONFIG}.tmp" "${SSH_CONFIG}"
fi
{
  echo "${BEGIN_MARK}"
  echo "Host github.com"
  echo "  HostName ssh.github.com"
  echo "  Port 443"
  echo "  User git"
  echo "  IdentityFile ${KEY}"
  echo "  IdentitiesOnly yes"
  echo "  BatchMode yes"
  echo "  PreferredAuthentications publickey"
  echo "${END_MARK}"
} >> "${SSH_CONFIG}"
chmod 600 "${SSH_CONFIG}"

# Seed host key for [ssh.github.com]:443 — do not scan github.com:22 (it times out).
touch "${KNOWN}"
chmod 600 "${KNOWN}"
ssh-keygen -R "[ssh.github.com]:443" -f "${KNOWN}" >/dev/null 2>&1 || true
ssh-keygen -R ssh.github.com -f "${KNOWN}" >/dev/null 2>&1 || true
ssh-keyscan -p 443 -t ed25519 ssh.github.com >> "${KNOWN}" 2>/dev/null
if ! ssh-keygen -F "[ssh.github.com]:443" -f "${KNOWN}" >/dev/null 2>&1; then
  echo "ssh-keyscan -p 443 ssh.github.com did not write a host key to ${KNOWN}." >&2
  exit 1
fi

# GIT_SSH_COMMAND still forces -i and 443 even if config is skipped.
export GIT_SSH_COMMAND="ssh -i \"${KEY}\" -p 443 -o HostName=ssh.github.com -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o BatchMode=yes"

set +e
ssh_out="$(ssh -i "${KEY}" -p 443 -o HostName=ssh.github.com -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o BatchMode=yes -T git@github.com 2>&1)"
set -e
if ! grep -qi "successfully authenticated" <<<"${ssh_out}"; then
  echo "GitHub SSH failed on ssh.github.com:443 without asking for a password." >&2
  echo "ssh used -i ${KEY} -p 443. Add the matching public key as a read-only deploy key." >&2
  if [[ -f "${KEY}.pub" ]]; then
    echo "Public key:" >&2
    cat "${KEY}.pub" >&2
  fi
  echo "${ssh_out}" >&2
  exit 2
fi

if [[ -d "${DEST}/.git" ]]; then
  origin="$(git -C "${DEST}" remote get-url origin 2>/dev/null || true)"
  case "${origin}" in
    https://*|http://*)
      echo "origin is HTTPS (${origin}). HTTPS is refused (hangs with no TTY)." >&2
      echo "Rewriting origin to ${REPO_SSH} and continuing over SSH." >&2
      git -C "${DEST}" remote set-url origin "${REPO_SSH}"
      ;;
  esac
  echo "Repo already at ${DEST}"
  git -C "${DEST}" remote -v
  exit 0
fi

if [[ -e "${DEST}" ]]; then
  echo "${DEST} exists but is not a git checkout (often a hung HTTPS clone)." >&2
  echo "Move it aside, then retry:  mv ${DEST} ${DEST}.stalled" >&2
  exit 1
fi

git -c credential.helper= clone "${REPO_SSH}" "${DEST}"
echo "Cloned ${REPO_SSH} to ${DEST}"
